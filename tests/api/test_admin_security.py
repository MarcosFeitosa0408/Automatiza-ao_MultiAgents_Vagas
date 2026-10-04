"""Permissões reais, sem substituir a autenticação por mocks."""
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
import main
from core.accounts import get_store

PASSWORD = 'Senha longa sintética 123!'


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.delenv('ACCOUNT_DATABASE_URL', raising=False)
    monkeypatch.setenv('ACCOUNT_DATABASE_PATH', str(tmp_path / 'accounts.sqlite3'))
    assert not main.app.dependency_overrides
    with TestClient(main.app) as client:
        yield client


def signup(client, email):
    response = client.post('/auth/register', json={'email': email, 'name': 'Teste', 'password': PASSWORD})
    assert response.status_code == 201
    assert response.json()['pending_approval']
    assert 'access_token' not in response.json()
    with get_store().connection() as db:
        return db.execute('SELECT id FROM users WHERE email=?', (email,)).fetchone()['id']


def login(client, email):
    response = client.post('/auth/login', json={'email': email, 'password': PASSWORD})
    assert response.status_code == 200, response.text
    return {'Authorization': 'Bearer ' + response.json()['access_token']}


def owner(client):
    identifier = signup(client, 'owner@example.invalid')
    get_store().bootstrap_admin('owner@example.invalid', PASSWORD)
    return identifier, login(client, 'owner@example.invalid')


def test_no_first_signup_or_payload_can_claim_administrator(client):
    identifier = signup(client, 'new@example.invalid')
    denied = client.post('/auth/login', json={'email': 'new@example.invalid', 'password': PASSWORD})
    assert denied.status_code == 403 and 'aguarda' in denied.json()['detail']
    forged = client.post('/auth/register', json={'email': 'fake@example.invalid', 'name': 'Fake', 'password': PASSWORD, 'role': 'admin', 'state': 'active'})
    assert forged.status_code == 422
    with get_store().connection() as db:
        assert db.execute('SELECT role, state FROM account_access WHERE user_id=?', (identifier,)).fetchone()['role'] == 'user'
    with pytest.raises(HTTPException):
        get_store().issue_session(identifier)
    assert client.get('/admin/users').status_code == 401


def test_authorize_block_reactivate_revokes_sessions_and_preserves_data(client):
    _, admin = owner(client)
    target = signup(client, 'member@example.invalid')
    approved = client.patch(f'/admin/users/{target}/access', headers=admin, json={'action': 'authorize'})
    assert approved.status_code == 200 and approved.json()['state'] == 'active'
    member = login(client, 'member@example.invalid')
    profile = client.get('/profile', headers=member).json()
    profile['professional_positioning']['summary'] = 'Conteúdo privado preservado'
    assert client.put('/profile', headers=member, json=profile).status_code == 200
    assert client.patch(f'/admin/users/{target}/access', headers=admin, json={'action': 'block'}).status_code == 200
    assert client.get('/profile', headers=member).status_code == 401
    assert client.post('/auth/login', json={'email': 'member@example.invalid', 'password': PASSWORD}).status_code == 403
    assert client.patch(f'/admin/users/{target}/access', headers=admin, json={'action': 'reactivate'}).status_code == 200
    assert client.get('/profile', headers=member).status_code == 401
    fresh = login(client, 'member@example.invalid')
    assert client.get('/profile', headers=fresh).json()['professional_positioning']['summary'] == 'Conteúdo privado preservado'
    assert client.patch(f'/admin/users/{target}/access', headers=admin, json={'action': 'reactivate'}).status_code == 409


def test_regular_user_cannot_list_or_change_or_delete_accounts(client):
    admin_id, admin = owner(client)
    target = signup(client, 'member@example.invalid')
    client.patch(f'/admin/users/{target}/access', headers=admin, json={'action': 'authorize'})
    member = login(client, 'member@example.invalid')
    assert client.get('/admin/users', headers=member).status_code == 403
    assert client.patch(f'/admin/users/{admin_id}/access', headers=member, json={'action': 'block'}).status_code == 403
    assert client.request('DELETE', f'/admin/users/{admin_id}', headers=member, json={'confirmation_email': 'owner@example.invalid'}).status_code == 403
    rows = client.get('/admin/users', headers=admin).json()
    assert all(set(row) == {'id', 'name', 'email', 'role', 'state'} for row in rows)


def test_admin_account_is_protected_and_second_bootstrap_is_rejected(client):
    admin_id, admin = owner(client)
    for action in ('authorize', 'block', 'reactivate'):
        assert client.patch(f'/admin/users/{admin_id}/access', headers=admin, json={'action': action}).status_code == 403
    assert client.request('DELETE', f'/admin/users/{admin_id}', headers=admin, json={'confirmation_email': 'owner@example.invalid'}).status_code == 403
    signup(client, 'member@example.invalid')
    with pytest.raises(ValueError):
        get_store().bootstrap_admin('member@example.invalid', PASSWORD)
    assert client.get('/admin/users', headers=admin).status_code == 200


def test_delete_requires_confirmation_and_removes_only_target(client):
    _, admin = owner(client)
    target = signup(client, 'member@example.invalid')
    client.patch(f'/admin/users/{target}/access', headers=admin, json={'action': 'authorize'})
    member = login(client, 'member@example.invalid')
    payload = {'application_id': 'same', 'job': {'job_id': 'j', 'title': 'Teste', 'company': 'Teste', 'source': 'TESTE'}}
    assert client.post('/job-applications', headers=member, json=payload).status_code == 200
    assert client.post('/job-applications', headers=admin, json=payload).status_code == 200
    bad = client.request('DELETE', f'/admin/users/{target}', headers=admin, json={'confirmation_email': 'wrong@example.invalid'})
    assert bad.status_code == 422
    assert client.get('/profile', headers=member).status_code == 200
    removed = client.request('DELETE', f'/admin/users/{target}', headers=admin, json={'confirmation_email': 'member@example.invalid'})
    assert removed.status_code == 200 and removed.json() == {'deleted': True, 'user_id': target}
    assert client.get('/profile', headers=member).status_code == 401
    assert client.get('/job-applications', headers=admin).json()[0]['application_id'] == 'same'
    with get_store().connection() as db:
        for table in ('profiles', 'sessions', 'account_access', 'private_applications'):
            assert db.execute(f'SELECT COUNT(*) FROM {table} WHERE user_id=?', (target,)).fetchone()[0] == 0
        assert db.execute("SELECT COUNT(*) FROM admin_audit WHERE target_id=? AND action='delete'", (target,)).fetchone()[0] == 1


def test_existing_sqlite_account_keeps_profile_and_jobs(tmp_path):
    import sqlite3
    from core.accounts import AccountStore, AccountMemoryAgent, AccountJobRepository, password_hash, empty_profile
    from core.schemas.job_application import JobApplicationObject
    path = tmp_path / 'old.sqlite3'
    # Simula um banco anterior sem metadados de autorização.
    with sqlite3.connect(path) as db:
        db.execute('CREATE TABLE users (id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, name TEXT NOT NULL, password_hash TEXT NOT NULL)')
        db.execute('CREATE TABLE profiles (user_id TEXT PRIMARY KEY, payload TEXT NOT NULL)')
        db.execute('INSERT INTO users VALUES (?, ?, ?, ?)', ('owner', 'old@example.invalid', 'Owner', password_hash.hash(PASSWORD)))
        profile = empty_profile('owner', 'Owner', 'old@example.invalid')
        profile.professional_positioning.summary = 'Dados existentes'
        db.execute('INSERT INTO profiles VALUES (?, ?)', ('owner', profile.model_dump_json()))
    store = AccountStore(str(path))
    repo = AccountJobRepository(store, 'owner')
    job = JobApplicationObject.model_validate({'application_id': 'old', 'job': {'job_id': 'j', 'title': 'Teste', 'company': 'Teste', 'source': 'TESTE'}})
    repo.save(job)
    store.bootstrap_admin('old@example.invalid', PASSWORD)
    assert store.check_password('old@example.invalid', PASSWORD)['role'] == 'admin'
    assert AccountMemoryAgent(store, 'owner').get_profile().professional_positioning.summary == 'Dados existentes'
    assert repo.get('old') == job

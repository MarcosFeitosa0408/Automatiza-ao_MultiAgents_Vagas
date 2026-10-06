import time
import pytest
from fastapi.testclient import TestClient
import main
from core.accounts import get_store
PASSWORD = 'Senha de teste longa 123!'

@pytest.fixture
def accounts(tmp_path, monkeypatch):
    monkeypatch.setenv('ACCOUNT_DATABASE_PATH', str(tmp_path / 'accounts.sqlite3'))
    assert not main.app.dependency_overrides
    with TestClient(main.app) as client:
        yield client

def register(client, email='a@example.invalid'):
    response = client.post('/auth/register', json={'email': email, 'name': 'Teste', 'password': PASSWORD})
    assert response.status_code == 201, response.text
    assert response.json()['pending_approval'] is True
    assert 'access_token' not in response.json()
    store = get_store()
    with store.connection() as db:
        target = db.execute('SELECT id FROM users WHERE email=?', (email,)).fetchone()['id']
        admin = db.execute("SELECT user_id FROM account_access WHERE role='admin'").fetchone()
    if admin:
        store.change_access(admin['user_id'], target, 'authorize')
    else:
        store.bootstrap_admin(email, PASSWORD)
    result = client.post('/auth/login', json={'email': email, 'password': PASSWORD})
    assert result.status_code == 200, result.text
    return result.json()

def headers(session):
    return {'Authorization': 'Bearer ' + session['access_token']}

def test_requires_login_for_every_private_route(accounts):
    from fastapi.routing import APIRoute
    for route in main.app.routes:
        if not isinstance(route, APIRoute) or route.path == '/health' or route.path.startswith('/auth/'):
            continue
        path = route.path.replace('{application_id}', 'other-user-id')
        for method in route.methods:
            response = accounts.request(method, path, json={})
            assert response.status_code == 401, (method, path, response.text)

def test_registration_blank_profile_and_password_hash(accounts):
    session = register(accounts)
    profile = accounts.get('/profile', headers=headers(session)).json()
    assert profile['candidate']['name'] == 'Teste'
    assert profile['experience'] == [] and profile['skills']['core'] == []
    with get_store().connection() as db:
        row = db.execute('SELECT password_hash FROM users').fetchone()
        assert row[0].startswith('$argon2id$') and PASSWORD not in row[0]
    assert 'password' not in session['user']

def test_two_accounts_isolate_all_application_operations(accounts):
    a, b = register(accounts), register(accounts, 'b@example.invalid')
    payload = {'application_id': 'only-a', 'job': {'job_id': 'job-a', 'title': 'Cargo privado A', 'company': 'Empresa', 'source': 'TESTE', 'requirements': ['SQL']}}
    assert accounts.post('/job-applications', headers=headers(a), json=payload).status_code == 200
    assert accounts.get('/job-applications', headers=headers(b)).json() == []
    paths = [('', 'GET'), ('', 'DELETE'), ('/qualify', 'POST'), ('/personalize', 'POST'), ('/prepare', 'POST'), ('/approve', 'POST'), ('/reject', 'POST'), ('/resume-preview', 'POST'), ('/interview-plan', 'POST'), ('/tracking/start', 'POST'), ('/tracking/status', 'POST'), ('/follow-up/check', 'POST'), ('/follow-up/register', 'POST'), ('/job-details', 'PATCH')]
    for suffix, method in paths:
        body = {'new_status': 'APPLIED'} if suffix == '/tracking/status' else {'requirements': ['Python']} if suffix == '/job-details' else None
        response = accounts.request(method, '/job-applications/only-a' + suffix, headers=headers(b), json=body)
        assert response.status_code == 404, (suffix, response.text)
    payload['job']['title'] = 'Cargo privado B'
    assert accounts.post('/job-applications', headers=headers(b), json=payload).status_code == 200
    assert accounts.get('/job-applications/only-a', headers=headers(a)).json()['job']['title'] == 'Cargo privado A'

def test_profile_isolation_persistence_logout_expiration(accounts):
    a, b = register(accounts), register(accounts, 'b@example.invalid')
    profile = accounts.get('/profile', headers=headers(a)).json()
    profile['candidate']['name'] = 'Nome privado A'
    profile['candidate_id'] = b['user']['id']
    result = accounts.put('/profile', headers=headers(a), json=profile)
    assert result.status_code == 200
    assert result.json()['candidate_id'] == a['user']['id']
    assert accounts.get('/profile', headers=headers(b)).json()['candidate']['name'] == 'Teste'
    assert accounts.post('/auth/logout', headers=headers(a)).status_code == 200
    assert accounts.get('/profile', headers=headers(a)).status_code == 401
    login = accounts.post('/auth/login', json={'email': 'A@EXAMPLE.INVALID', 'password': PASSWORD}).json()
    with TestClient(main.app) as fresh_client:
        assert fresh_client.get('/profile', headers=headers(login)).json()['candidate']['name'] == 'Nome privado A'
    with get_store().connection() as db:
        db.execute('UPDATE sessions SET expires_at=?', (time.time() - 1,))
    assert accounts.get('/profile', headers=headers(login)).status_code == 401

def test_invalid_credentials_validation_and_rate_limit(accounts):
    register(accounts)
    bad = accounts.post('/auth/login', json={'email': 'a@example.invalid', 'password': 'Outra senha longa 123!'})
    assert bad.status_code == 401
    short = accounts.post('/auth/register', json={'email': 'x@example.invalid', 'name': 'X', 'password': 'short7'})
    assert short.status_code == 422 and 'short7' not in short.text
    assert accounts.get('/profile', headers={'Authorization': 'Bearer garbage'}).status_code == 401
    with get_store().connection() as db:
        db.executemany('INSERT INTO attempts VALUES (?, ?)', [('login:testclient', time.time())] * 20)
    assert accounts.post('/auth/login', json={'email': 'a@example.invalid', 'password': PASSWORD}).status_code == 429

def test_edit_requirements_persists_and_resets_analysis(accounts):
    a = register(accounts)
    h = headers(a)
    payload = {'application_id': 'editable', 'job': {'job_id': 'job', 'title': 'Cargo', 'company': 'Empresa', 'source': 'TESTE'}}
    original = accounts.post('/job-applications', headers=h, json=payload).json()
    bad = accounts.patch('/job-applications/editable/job-details', headers=h, json={'requirements': ['  ']})
    assert bad.status_code == 422
    result = accounts.patch('/job-applications/editable/job-details', headers=h, json={'description': 'Texto real', 'requirements': [' SQL ', 'SQL'], 'desirable_requirements': ['Python']})
    assert result.status_code == 200
    assert result.json()['job']['requirements'] == ['SQL']
    assert result.json()['job']['job_id'] == original['job']['job_id']
    assert accounts.get('/job-applications/editable', headers=h).json() == result.json()

def test_owner_can_generate_resume_interview_and_metrics_are_private(accounts):
    import json
    from pathlib import Path
    a, b = register(accounts), register(accounts, 'b@example.invalid')
    profile = json.loads(Path('tests/fixtures/profile.json').read_text())
    profile['candidate']['name'] = 'Nome privado para currículo'
    assert accounts.put('/profile', headers=headers(a), json=profile).status_code == 200
    payload = {'application_id': 'pipeline', 'job': {'job_id': 'job', 'title': 'Analista de Dados', 'company': 'Empresa Teste', 'source': 'TESTE', 'requirements': ['SQL', 'Power BI']}}
    assert accounts.post('/job-applications', headers=headers(a), json=payload).status_code == 200
    preview = accounts.post('/job-applications/pipeline/resume-preview', headers=headers(a))
    assert preview.status_code == 200, preview.text
    assert preview.json()['name'] == 'Nome privado para currículo'
    plan = accounts.post('/job-applications/pipeline/interview-plan', headers=headers(a))
    assert plan.status_code == 200, plan.text
    assert plan.json()['questions']
    from core.accounts import AccountJobRepository
    from core.schemas.tracking import ApplicationTracking
    repository = AccountJobRepository(get_store(), a['user']['id'])
    application = repository.get('pipeline')
    application.tracking = ApplicationTracking(job_id='job', current_status='APPLIED', history=[])
    repository.save(application)
    assert accounts.get('/job-applications/metrics', headers=headers(a)).json()['total_applications'] == 1
    assert accounts.get('/job-applications/metrics', headers=headers(b)).json()['total_applications'] == 0
    assert accounts.post('/opportunities/search', json={'query': 'SQL', 'country': 'br'}).status_code == 401

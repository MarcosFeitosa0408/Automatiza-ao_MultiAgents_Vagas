from datetime import datetime, timezone
from uuid import uuid4
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
import main
from core.accounts import AccountStore
from core import help_api


@pytest.fixture
def setup(tmp_path, monkeypatch):
    store = AccountStore(str(tmp_path / 'accounts.sqlite3'))
    monkeypatch.setattr('core.auth_api.get_store', lambda: store)
    monkeypatch.setattr(help_api, 'get_store', lambda: store)
    admin = store.create_user('Admin', 'admin@example.invalid', 'Senha1234!')
    store.bootstrap_admin(admin['email'], 'Senha1234!')
    user = store.create_user('Pessoa', 'user@example.invalid', 'Senha1234!')
    store.change_access(admin['id'], user['id'], 'authorize')
    admin = store.check_password(admin['email'], 'Senha1234!')
    user = store.check_password(user['email'], 'Senha1234!')
    with TestClient(main.app) as client:
        yield store, client, admin, user


def headers(store, user):
    return {'Authorization': 'Bearer ' + store.issue_session(user['id'])}


def send(client, auth, question, request_id=None):
    return client.post('/help/forward', headers=auth, json={'question': question, 'request_id': str(request_id or uuid4())})


def test_consent_quota_dedup_and_admin_access(setup):
    store, client, admin, user = setup
    auth = headers(store, user)
    assert client.get('/help').status_code == 401
    assert client.get('/admin/help/questions', headers=auth).status_code == 403
    known = client.post('/help/ask', headers=auth, json={'question': 'Como salvar o PDF?'})
    assert known.json()['known'] is True
    unknown = 'Posso escolher a cor do painel?'
    assert client.post('/help/ask', headers=auth, json={'question': unknown}).json()['remaining'] == 3
    with store.connection() as db:
        assert db.execute('SELECT COUNT(*) FROM help_questions').fetchone()[0] == 0
    key = uuid4()
    assert send(client, auth, unknown, key).json()['remaining'] == 2
    assert send(client, auth, unknown, key).json()['duplicate'] is True
    assert send(client, auth, unknown.upper()).json()['remaining'] == 2
    assert send(client, auth, 'Uma outra pergunta desconhecida', key).status_code == 409
    assert send(client, auth, 'Há um modo para organizar o painel?').status_code == 200
    assert send(client, auth, 'Posso reorganizar os cartões?').status_code == 200
    assert send(client, auth, 'Posso escolher uma fonte maior?').status_code == 429
    assert client.post('/help/ask', headers=auth, json={'question': 'Como salvar o PDF?'}).json()['known']
    assert send(client, auth, 'Como salvar o PDF?').status_code == 409
    adm = headers(store, admin)
    for i in range(4):
        assert send(client, adm, f'Outra dúvida desconhecida número {i}').json()['remaining'] is None
    history = client.get('/admin/help/questions', headers=adm).json()
    item = history['items'][0]
    assert client.patch('/admin/help/questions/' + item['id'], headers=adm, json={'state':'answered','answer':''}).status_code == 422
    assert client.patch('/admin/help/questions/' + item['id'], headers=adm, json={'state':'answered','answer':'Orientação revisada.'}).status_code == 200
    exported = client.get('/admin/help/export', headers=adm)
    assert user['email'] not in exported.text and user['id'] not in exported.text
    assert client.delete('/admin/help/questions/' + item['id'], headers=adm).status_code == 200
    assert client.get('/help', headers=auth).json()['remaining'] == 0
    monkeypatch_period = lambda: ('2030-01-07', '2030-01-14T00:00:00-03:00')
    old = help_api.period
    try:
        help_api.period = monkeypatch_period
        assert client.get('/help', headers=auth).json()['remaining'] == 3
    finally:
        help_api.period = old


def test_block_privacy_and_cascade(setup):
    store, client, admin, user = setup
    auth = headers(store, user)
    assert send(client, auth, 'Meu contato é pessoa@example.invalid').status_code == 422
    assert send(client, auth, 'Quero mudar a cor do painel').status_code == 200
    store.change_access(admin['id'], user['id'], 'block')
    assert client.get('/help', headers=auth).status_code == 401
    store.delete_account(admin['id'], user['id'], user['email'])
    with store.connection() as db:
        assert db.execute('SELECT COUNT(*) FROM help_questions').fetchone()[0] == 0
        assert db.execute('SELECT COUNT(*) FROM help_usage').fetchone()[0] == 0


def test_concurrent_limit(setup):
    store, _, _, user = setup
    for text in ('Posso escolher a cor?', 'Posso mover os cartões?'):
        help_api.forward(help_api.Forward(question=text, request_id=uuid4()), user)
    def attempt(i):
        try:
            help_api.forward(help_api.Forward(question=f'Pergunta desconhecida concorrente {i}', request_id=uuid4()), user)
            return 200
        except HTTPException as error:
            return error.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(attempt, range(2))) == [200, 429]


def test_week_boundary():
    sunday = datetime(2026, 10, 12, 2, 59, tzinfo=timezone.utc).timestamp()
    monday = datetime(2026, 10, 12, 3, 0, tzinfo=timezone.utc).timestamp()
    assert help_api.period(sunday)[0] == '2026-10-05'
    assert help_api.period(monday)[0] == '2026-10-12'

import time
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
import main
from core.accounts import AccountStore, AccountMemoryAgent
from core import password_recovery as recovery

OLD = 'Senha antiga longa 123!'
NEW = 'Senha nova longa segura 456!'

@pytest.fixture
def setup(tmp_path, monkeypatch):
    store = AccountStore(str(tmp_path / 'accounts.sqlite3'))
    monkeypatch.setattr('core.auth_api.get_store', lambda: store)
    monkeypatch.setenv('BREVO_API_KEY', 'fake-test-key')
    monkeypatch.setenv('RECOVERY_FROM_EMAIL', 'sender@example.invalid')
    monkeypatch.setenv('PUBLIC_APP_URL', 'https://example.invalid')
    sent = []
    monkeypatch.setattr(recovery, 'send_recovery_email', lambda email, token, settings: sent.append((email, token)))
    with TestClient(main.app) as client:
        yield store, client, sent


def request(client, email):
    return client.post('/auth/forgot-password', json={'email': email})


def test_recovery_single_use_preserves_profile_and_revokes_sessions(setup):
    store, client, sent = setup
    user = store.create_user('Test', 'user@example.invalid', OLD)
    store.bootstrap_admin(user['email'], OLD)
    session = store.issue_session(user['id'])
    before = AccountMemoryAgent(store, user['id']).get_profile()
    assert request(client, user['email']).status_code == 202
    token = sent[0][1]
    with store.connection() as db:
        assert db.execute('SELECT token_hash FROM password_resets').fetchone()[0] != token
    result = client.post('/auth/reset-password', json={'token': token, 'password': NEW})
    assert result.status_code == 200
    assert store.check_password(user['email'], NEW)['role'] == 'admin'
    with pytest.raises(HTTPException): store.current_user(session)
    with pytest.raises(HTTPException): store.check_password(user['email'], OLD)
    assert AccountMemoryAgent(store, user['id']).get_profile() == before
    assert client.post('/auth/reset-password', json={'token': token, 'password': OLD}).status_code == 400


@pytest.mark.parametrize('state', ['pending', 'blocked'])
def test_recovery_never_authorizes_an_account(setup, state):
    store, client, sent = setup
    user = store.create_user('Test', 'user@example.invalid', OLD)
    with store.connection() as db:
        db.execute('UPDATE account_access SET state=? WHERE user_id=?', (state, user['id']))
    request(client, user['email'])
    assert client.post('/auth/reset-password', json={'token': sent[0][1], 'password': NEW}).status_code == 200
    with pytest.raises(HTTPException) as denied: store.check_password(user['email'], NEW)
    assert denied.value.status_code == 403
    with store.connection() as db:
        assert db.execute('SELECT state FROM account_access').fetchone()[0] == state


def test_expired_invalid_and_password_validation(setup):
    store, client, sent = setup
    user = store.create_user('Test', 'user@example.invalid', OLD)
    request(client, user['email'])
    token = sent[0][1]
    bad = client.post('/auth/reset-password', json={'token': token, 'password': 'short'})
    assert bad.status_code == 422 and token not in bad.text
    with store.connection() as db: db.execute('UPDATE password_resets SET expires_at=?', (time.time() - 1,))
    assert client.post('/auth/reset-password', json={'token': token, 'password': NEW}).status_code == 400
    assert client.post('/auth/reset-password', json={'token': 'x'*64, 'password': NEW}).status_code == 400


def test_generic_response_configuration_and_rate_limit(setup, monkeypatch):
    store, client, sent = setup
    store.create_user('Test', 'user@example.invalid', OLD)
    assert request(client, 'user@example.invalid').json() == request(client, 'unknown@example.invalid').json()
    assert len(sent) == 1
    request(client, 'user@example.invalid');request(client, 'user@example.invalid')
    assert request(client, 'user@example.invalid').status_code == 429
    monkeypatch.delenv('BREVO_API_KEY')
    assert request(client, 'another@example.invalid').status_code == 503


def test_delivery_failure_does_not_leak_or_leave_token(setup, monkeypatch, caplog):
    store, client, sent = setup
    store.create_user('Test', 'user@example.invalid', OLD)
    def fail(*args): raise RuntimeError('secret-must-not-appear')
    monkeypatch.setattr(recovery, 'send_recovery_email', fail)
    result = request(client, 'user@example.invalid')
    assert result.status_code == 202
    assert 'secret-must-not-appear' not in caplog.text
    with store.connection() as db: assert db.execute('SELECT COUNT(*) FROM password_resets').fetchone()[0] == 0


def test_deletion_removes_recovery_tokens(setup):
    store, client, sent = setup
    admin = store.create_user('Owner', 'owner@example.invalid', OLD)
    store.bootstrap_admin(admin['email'], OLD)
    member = store.create_user('Member', 'member@example.invalid', OLD)
    request(client, member['email'])
    store.delete_account(admin['id'], member['id'], member['email'])
    assert client.post('/auth/reset-password', json={'token': sent[0][1], 'password': NEW}).status_code == 400


def test_two_concurrent_uses_only_one_succeeds(setup):
    from concurrent.futures import ThreadPoolExecutor
    store, client, sent = setup
    store.create_user('Test', 'user@example.invalid', OLD)
    request(client, 'user@example.invalid')
    token = sent[0][1]
    def consume(_):
        try:
            recovery.reset_password(store, token, NEW)
            return 200
        except HTTPException as error:
            return error.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(consume, [1, 2])) == [200, 400]


def test_provider_request_uses_expected_fields(monkeypatch):
    recorded = []
    class Client:
        def __init__(self, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def post(self, url, **kwargs):
            recorded.append((url, kwargs))
            return httpx.Response(201, request=httpx.Request('POST', url))
    import httpx
    monkeypatch.setattr(recovery.httpx, 'Client', Client)
    recovery.send_recovery_email('user@example.invalid', 'a'*64, ('fake-key', 'sender@example.invalid', 'https://example.invalid'))
    url, options = recorded[0]
    assert url == 'https://api.brevo.com/v3/smtp/email'
    assert options['headers']['api-key'] == 'fake-key'
    assert options['json']['to'] == [{'email': 'user@example.invalid'}]
    assert 'https://example.invalid/#/redefinir-senha?token=' in options['json']['textContent']

from fastapi.testclient import TestClient
import main
from core.accounts import get_store, AccountJobRepository
from core.schemas.job_application import JobApplicationObject
from core.orchestrator.orchestrator import JobOrchestrator


def test_feedback_requires_login_and_owns_application(tmp_path, monkeypatch):
    monkeypatch.delenv('ACCOUNT_DATABASE_URL', raising=False)
    monkeypatch.setenv('ACCOUNT_DATABASE_PATH', str(tmp_path / 'accounts.sqlite3'))
    # Legacy fixtures restore bound instance methods; use a fresh orchestrator
    # so this test exercises the real per-account repository dependencies.
    monkeypatch.setattr(main, 'orchestrator', JobOrchestrator())
    store = get_store()
    password = 'Senha de teste longa 123!'
    owner = store.create_user('Owner', 'owner@example.invalid', password)
    store.bootstrap_admin(owner['email'], password)
    other = store.create_user('Other', 'other@example.invalid', password)
    store.change_access(owner['id'], other['id'], 'authorize')
    job = JobApplicationObject.model_validate({'application_id': 'private', 'job': {
        'job_id': 'test', 'title': 'Analista', 'company': 'Empresa', 'source': 'TEST', 'requirements': ['SQL']}})
    AccountJobRepository(store, owner['id']).save(job)
    auth = lambda user: {'Authorization': 'Bearer ' + store.issue_session(user['id'])}
    body = {'question_id': 'presentation', 'answer': 'Estou estudando análise de dados.'}
    path = '/job-applications/private/interview-feedback'
    with TestClient(main.app) as client:
        assert client.post(path, json=body).status_code == 401
        assert client.post(path, json=body, headers=auth(other)).status_code == 404
        with store.connection() as db:
            before = {table: [tuple(r) for r in db.execute('SELECT * FROM ' + table).fetchall()]
                      for table in ('profiles', 'private_applications')}
        assert client.post(path, json=body, headers=auth(owner)).status_code == 200
        with store.connection() as db:
            for table, rows in before.items():
                assert [tuple(r) for r in db.execute('SELECT * FROM ' + table).fetchall()] == rows

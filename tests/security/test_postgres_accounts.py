"""Testes em esquema temporário; nunca usam perfis reais nem removem tabelas públicas."""
import os
from contextlib import contextmanager
from uuid import uuid4

import psycopg
from psycopg import sql
import pytest
from fastapi import HTTPException
from core import accounts
from core.accounts import AccountMemoryAgent, AccountJobRepository, PostgresAccountStore
from core.schemas.job_application import JobApplicationObject


def test_invalid_url_is_rejected_without_creating_local_database(tmp_path, monkeypatch):
    monkeypatch.setenv('ACCOUNT_DATABASE_URL', 'invalid://example')
    destination = tmp_path / 'local.sqlite3'
    monkeypatch.setenv('ACCOUNT_DATABASE_PATH', str(destination))
    with pytest.raises(ValueError, match='Postgres'):
        accounts.get_store()
    assert not destination.exists()


def test_postgres_rejects_disabled_ssl():
    with pytest.raises(ValueError, match='SSL'):
        PostgresAccountStore('postgresql://example.invalid/db?sslmode=disable')


def active_user(store, name, email, password):
    user = store.create_user(name, email, password)
    with store.connection() as db:
        admin = db.execute("SELECT user_id FROM account_access WHERE role='admin'").fetchone()
    if not admin:
        return store.bootstrap_admin(email, password)
    return store.change_access(admin['user_id'], user['id'], 'authorize')


@pytest.fixture
def pg_store():
    url = os.getenv('TEST_ACCOUNT_POSTGRES_URL', '').strip()
    if not url:
        pytest.skip('Configure TEST_ACCOUNT_POSTGRES_URL para testar um Postgres real.')
    schema = 'account_test_' + uuid4().hex
    with psycopg.connect(url) as db:
        db.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))

    class IsolatedStore(PostgresAccountStore):
        @contextmanager
        def connection(self):
            with psycopg.connect(**self._options, connect_timeout=15,
                                 row_factory=accounts._account_row_factory,
                                 prepare_threshold=None) as db:
                db.execute(sql.SQL('SET LOCAL search_path TO {}').format(sql.Identifier(schema)))
                yield accounts._PostgresConnection(db)
    try:
        yield IsolatedStore(url)
    finally:
        with psycopg.connect(url) as db:
            db.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


def test_postgres_login_sessions_and_duplicate_email(pg_store):
    user = active_user(pg_store, 'Teste', 'a@example.invalid', 'senha longa apenas de teste')
    assert pg_store.check_password(user['email'], 'senha longa apenas de teste') == user
    with pytest.raises(HTTPException) as wrong:
        pg_store.check_password(user['email'], 'incorreta')
    assert wrong.value.status_code == 401
    with pytest.raises(HTTPException) as duplicate:
        active_user(pg_store, 'Outro', user['email'], 'outra senha longa de teste')
    assert duplicate.value.status_code == 409
    token = pg_store.issue_session(user['id'])
    assert pg_store.current_user(token) == user
    pg_store.revoke(token)
    with pytest.raises(HTTPException):
        pg_store.current_user(token)


def test_postgres_profile_and_application_isolation(pg_store):
    a = active_user(pg_store, 'A', 'a@example.invalid', 'senha longa apenas de teste')
    b = active_user(pg_store, 'B', 'b@example.invalid', 'senha longa apenas de teste')
    memory = AccountMemoryAgent(pg_store, a['id'])
    profile = memory.get_profile()
    profile.professional_positioning.summary = 'Resumo sintético'
    memory.save_profile(profile)
    assert memory.get_profile().professional_positioning.summary == 'Resumo sintético'
    assert AccountMemoryAgent(pg_store, b['id']).get_profile().professional_positioning.summary == ''
    job = JobApplicationObject.model_validate({'application_id': 'same', 'job': {'job_id': 'j', 'title': 'Teste', 'company': 'Teste', 'source': 'TESTE'}})
    ra, rb = AccountJobRepository(pg_store, a['id']), AccountJobRepository(pg_store, b['id'])
    ra.save(job)
    rb.save(job)
    assert ra.get('same') is not None
    assert ra.delete('same')
    assert ra.list_all() == []
    assert rb.get('same') is not None
    assert not ra.delete('same')


def test_postgres_transaction_rolls_back_and_limits(pg_store):
    with pytest.raises(ValueError):
        with pg_store.connection() as db:
            db.execute('INSERT INTO attempts VALUES (?, ?)', ('rollback', 1))
            raise ValueError('abort')
    with pg_store.connection() as db:
        assert db.execute('SELECT COUNT(*) FROM attempts WHERE bucket=?', ('rollback',)).fetchone()[0] == 0
    pg_store.limit('test', maximum=1)
    with pytest.raises(HTTPException) as limited:
        pg_store.limit('test', maximum=1)
    assert limited.value.status_code == 429


def test_postgres_import_is_atomic_and_does_not_overwrite(pg_store, tmp_path):
    import json
    from pathlib import Path
    from core.import_private_backup import import_backup
    user = active_user(pg_store, 'A', 'a@example.invalid', 'senha longa apenas de teste')
    profile = json.loads(Path('tests/fixtures/profile.json').read_text(encoding='utf-8'))
    (tmp_path / 'MASTER_PROFILE.json').write_text(json.dumps(profile), encoding='utf-8')
    jobs = [{'application_id': 'saved', 'job': {'job_id': 'j', 'title': 'Teste', 'company': 'Teste', 'source': 'TESTE'}}]
    (tmp_path / 'job-applications.json').write_text(json.dumps(jobs), encoding='utf-8')
    assert import_backup(pg_store, user, tmp_path) == 1
    with pytest.raises(ValueError):
        import_backup(pg_store, user, tmp_path)
    assert len(AccountJobRepository(pg_store, user['id']).list_all()) == 1


def test_postgres_admin_lifecycle_revokes_access_and_deletes_only_member(pg_store):
    owner = active_user(pg_store, 'Owner', 'owner@example.invalid', 'senha longa apenas de teste')
    member = pg_store.create_user('Member', 'member@example.invalid', 'senha longa apenas de teste')
    with pytest.raises(HTTPException):
        pg_store.check_password(member['email'], 'senha longa apenas de teste')
    pg_store.change_access(owner['id'], member['id'], 'authorize')
    token = pg_store.issue_session(member['id'])
    pg_store.change_access(owner['id'], member['id'], 'block')
    with pytest.raises(HTTPException):
        pg_store.current_user(token)
    pg_store.change_access(owner['id'], member['id'], 'reactivate')
    with pytest.raises(HTTPException):
        pg_store.current_user(token)
    assert pg_store.check_password(member['email'], 'senha longa apenas de teste')['state'] == 'active'
    with pytest.raises(HTTPException):
        pg_store.delete_account(owner['id'], owner['id'], owner['email'])
    assert pg_store.delete_account(owner['id'], member['id'], member['email'])['deleted']
    assert len(pg_store.list_accounts(owner['id'])) == 1

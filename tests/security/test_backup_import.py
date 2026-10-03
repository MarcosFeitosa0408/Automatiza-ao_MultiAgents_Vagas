import json
from pathlib import Path
import pytest
from core.accounts import AccountStore, AccountMemoryAgent, AccountJobRepository
from core.import_private_backup import import_backup

@pytest.fixture
def backup(tmp_path):
    folder = tmp_path / 'backup'
    folder.mkdir()
    profile = json.loads(Path('tests/fixtures/profile.json').read_text())
    profile['candidate']['name'] = 'Perfil do backup'
    (folder / 'MASTER_PROFILE.json').write_text(json.dumps(profile), encoding='utf-8')
    data = [{'application_id': 'saved', 'job': {'job_id': 'job', 'title': 'Cargo salvo', 'company': 'Empresa', 'source': 'TESTE'}}]
    (folder / 'job-applications.json').write_text(json.dumps(data), encoding='utf-8')
    return folder

def test_import_preserves_backup_and_only_updates_authenticated_account(tmp_path, backup):
    store = AccountStore(str(tmp_path / 'accounts.sqlite3'))
    a = store.create_user('A', 'a@example.invalid', 'uma senha longa para teste')
    b = store.create_user('B', 'b@example.invalid', 'outra senha longa para teste')
    before = (backup / 'MASTER_PROFILE.json').read_bytes()
    assert import_backup(store, a, backup) == 1
    profile = AccountMemoryAgent(store, a['id']).get_profile()
    assert profile.candidate.name == 'Perfil do backup'
    assert profile.candidate_id == a['id']
    assert AccountMemoryAgent(store, b['id']).get_profile().experience == []
    assert AccountJobRepository(store, b['id']).list_all() == []
    assert (backup / 'MASTER_PROFILE.json').read_bytes() == before
    with pytest.raises(ValueError):
        import_backup(store, a, backup)
    assert len(AccountJobRepository(store, a['id']).list_all()) == 1

def test_invalid_backup_does_not_partially_import(tmp_path, backup):
    store = AccountStore(str(tmp_path / 'accounts.sqlite3'))
    a = store.create_user('A', 'a@example.invalid', 'uma senha longa para teste')
    (backup / 'job-applications.json').write_text('[{"job": {}}]', encoding='utf-8')
    with pytest.raises(ValueError):
        import_backup(store, a, backup)
    assert AccountMemoryAgent(store, a['id']).get_profile().experience == []
    assert AccountJobRepository(store, a['id']).list_all() == []

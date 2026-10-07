from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
import main
from core.accounts import AccountStore, AccountJobRepository
from core.job_identity import canonical_url, same_opportunity
from core.schemas.job_application import JobApplicationObject
from core.schemas.job import JobOpportunity


def application(job_id='job-1', source='Adzuna', url='https://example.invalid/jobs/1', app_id=None):
    return JobApplicationObject(application_id=app_id or str(uuid4()), job=JobOpportunity(job_id=job_id, source=source, title='Analista', company='Empresa', url=url, requirements=['SQL']))


@pytest.fixture
def setup(tmp_path, monkeypatch):
    store=AccountStore(str(tmp_path/'accounts.sqlite3'))
    monkeypatch.setattr('core.auth_api.get_store', lambda:store)
    monkeypatch.setattr('main.get_store', lambda:store)
    owner=store.create_user('Admin','admin@example.invalid','Senha1234!')
    store.bootstrap_admin(owner['email'],'Senha1234!')
    other=store.create_user('Pessoa','other@example.invalid','Senha1234!')
    store.change_access(owner['id'],other['id'],'authorize')
    return store,owner,other


def test_source_id_url_and_distinct_opportunities(setup):
    store,owner,other=setup
    repo=AccountJobRepository(store,owner['id'])
    first=repo.create_unique(application())
    with pytest.raises(HTTPException) as caught:
        repo.create_unique(application(url='https://example.invalid/redirect/other'))
    assert caught.value.detail['application_id']==first.application_id
    with pytest.raises(HTTPException):
        repo.create_unique(application(job_id='new',source='Manual',url='https://example.invalid/jobs/1?utm_source=newsletter#'))
    assert repo.get(first.application_id).job.requirements==['SQL']
    assert len(repo.list_all())==1
    repo.create_unique(application(job_id='job-2',url='https://example.invalid/jobs/2'))
    repo.create_unique(application(job_id='job-3',url=None))
    repo.create_unique(application(job_id='job-4',url=None))
    assert len(repo.list_all())==4
    AccountJobRepository(store,other['id']).create_unique(application())
    assert len(AccountJobRepository(store,other['id']).list_all())==1


def test_retry_cannot_reset_existing_data_and_deletion_releases_identity(setup):
    store,owner,_=setup;repo=AccountJobRepository(store,owner['id'])
    first=repo.create_unique(application())
    changed=first.model_copy(deep=True);changed.job.description='Requisitos completos editados'
    repo.save(changed)
    with pytest.raises(HTTPException):repo.create_unique(first)
    assert repo.get(first.application_id).job.description=='Requisitos completos editados'
    repo.delete(first.application_id)
    assert repo.create_unique(application()).application_id


def test_concurrent_create_keeps_one(setup):
    store,owner,_=setup;repo=AccountJobRepository(store,owner['id'])
    def create(_):
        try:repo.create_unique(application());return 200
        except HTTPException as error:return error.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(create,range(2)))==[200,409]
    assert len(repo.list_all())==1


def test_old_duplicates_are_preserved(setup):
    store,owner,_=setup;repo=AccountJobRepository(store,owner['id'])
    repo.save(application());repo.save(application())
    with pytest.raises(HTTPException):repo.create_unique(application())
    assert len(repo.list_all())==2


def test_api_409_only_exposes_owned_record(setup):
    store,owner,other=setup
    def auth(user):return {'Authorization':'Bearer '+store.issue_session(user['id'])}
    payload=application().model_dump(mode='json',include={'application_id','job'})
    with TestClient(main.app) as client:
        assert client.post('/job-applications',json=payload).status_code==401
        first=client.post('/job-applications',json=payload,headers=auth(owner))
        assert first.status_code==200
        payload['application_id']=str(uuid4())
        duplicate=client.post('/job-applications',json=payload,headers=auth(owner))
        assert duplicate.status_code==409
        assert duplicate.json()['detail']['application_id']==first.json()['application_id']
        assert client.post('/job-applications',json=payload,headers=auth(other)).status_code==200


def test_url_identity_parameters_and_fragments_preserved():
    assert canonical_url('https://EXAMPLE.invalid/jobs?id=1&utm_medium=mail')==canonical_url('https://example.invalid/jobs?id=1')
    assert not same_opportunity(application('1',url='https://example.invalid/jobs?id=1').job,application('2',url='https://example.invalid/jobs?id=2').job)
    assert not same_opportunity(application('1',url='https://example.invalid/#/jobs/1').job,application('2',url='https://example.invalid/#/jobs/2').job)
    assert not same_opportunity(application('same','Fonte A',None).job,application('same','Fonte B',None).job)

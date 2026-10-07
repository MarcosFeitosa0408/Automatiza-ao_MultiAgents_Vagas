from uuid import uuid4
from fastapi.testclient import TestClient
import main
from core.accounts import AccountStore, AccountJobRepository
from core.schemas.job import JobOpportunity
from core.schemas.job_application import JobApplicationObject


def test_confirmed_external_progress_updates_history_metrics_and_privacy(tmp_path,monkeypatch):
    store=AccountStore(str(tmp_path/'accounts.sqlite3'))
    for module in ('main','core.auth_api','core.progress_api'):
        monkeypatch.setattr(module+'.get_store',lambda:store)
    owner=store.create_user('Admin','admin@example.invalid','Senha1234!')
    store.bootstrap_admin(owner['email'],'Senha1234!')
    other=store.create_user('Outra','other@example.invalid','Senha1234!')
    store.change_access(owner['id'],other['id'],'authorize')
    repo=AccountJobRepository(store,owner['id'])
    app=repo.create_unique(JobApplicationObject(application_id=str(uuid4()),job=JobOpportunity(job_id='1',title='Analista',company='Empresa',source='Teste',requirements=['SQL'])))
    auth={'Authorization':'Bearer '+store.issue_session(owner['id'])}
    other_auth={'Authorization':'Bearer '+store.issue_session(other['id'])}
    path=f'/job-applications/{app.application_id}/progress'
    payload={'new_status':'APPLIED','expected_status':None,'confirmed':True,'note':'Envio confirmado no portal.'}
    with TestClient(main.app) as client:
        assert client.post(path,json=payload).status_code==401
        assert client.post(path,json=payload,headers=other_auth).status_code==404
        assert client.post(path,json={**payload,'confirmed':False},headers=auth).status_code==422
        assert repo.get(app.application_id).tracking is None
        sent=client.post(path,json=payload,headers=auth)
        assert sent.status_code==200 and sent.json()['tracking']['current_status']=='APPLIED'
        assert len(client.post(path,json=payload,headers=auth).json()['tracking']['history'])==1
        assert repo.get(app.application_id).job.requirements==['SQL']
        assert repo.get(app.application_id).preparation is None
        assert client.post(path,json={**payload,'new_status':'INTERVIEW','expected_status':None},headers=auth).status_code==409
        interview=client.post(path,json={**payload,'new_status':'INTERVIEW','expected_status':'APPLIED'},headers=auth)
        assert len(interview.json()['tracking']['history'])==2
        metrics=client.get('/job-applications/metrics',headers=auth).json()
        assert metrics['total_applications']==1 and metrics['interviews']==1 and metrics['interview_rate']==100.0
        assert client.post(path,json={**payload,'new_status':'HIRED','expected_status':'INTERVIEW'},headers=auth).status_code==200
        metrics=client.get('/job-applications/metrics',headers=auth).json()
        assert metrics['hires']==1 and metrics['interviews']==1 and metrics['offers']==0
        assert client.post(path,json={**payload,'new_status':'DISCOVERED'},headers=auth).status_code==422
        assert client.post(path,json={**payload,'note':'x'*1001},headers=auth).status_code==422
        direct=repo.create_unique(JobApplicationObject(application_id=str(uuid4()),job=JobOpportunity(job_id='2',title='Analista',company='Empresa',source='Teste')))
        assert client.post(f'/job-applications/{direct.application_id}/progress',json={**payload,'new_status':'HIRED'},headers=auth).status_code==200
        metrics=client.get('/job-applications/metrics',headers=auth).json()
        assert metrics['total_applications']==2 and metrics['hires']==2 and metrics['interviews']==1
        assert metrics['interview_rate']==50.0


def test_rejection_counts_as_response_without_inventing_interview(tmp_path,monkeypatch):
    from core.progress_api import record_progress, ProgressRequest
    from core.orchestrator.orchestrator import JobOrchestrator
    store=AccountStore(str(tmp_path/'accounts.sqlite3'))
    monkeypatch.setattr('core.progress_api.get_store',lambda:store)
    user=store.create_user('Pessoa','person@example.invalid','Senha1234!')
    repo=AccountJobRepository(store,user['id'])
    app=repo.save(JobApplicationObject(application_id='one',job=JobOpportunity(job_id='1',title='Analista',company='Empresa',source='Teste')))
    record_progress(app.application_id,ProgressRequest(new_status='REJECTED',confirmed=True),user)
    metrics=JobOrchestrator().calculate_job_application_metrics(repo.list_all())
    assert metrics['response_rate']==100.0
    assert metrics['screening_or_beyond']==metrics['interviews']==metrics['offers']==metrics['hires']==0

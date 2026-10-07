from uuid import uuid4
from fastapi.testclient import TestClient
import main
from core.accounts import AccountStore, AccountJobRepository
from core.schemas.job import JobOpportunity, JobStatus
from core.schemas.job_application import JobApplicationObject
from core.schemas.tracking import ApplicationTracking


def test_dashboard_counts_saved_jobs_and_preserves_real_stages(tmp_path, monkeypatch):
    store=AccountStore(str(tmp_path/'accounts.sqlite3'))
    monkeypatch.setattr('main.get_store',lambda:store)
    monkeypatch.setattr('core.auth_api.get_store',lambda:store)
    admin=store.create_user('Admin','admin@example.invalid','Senha1234!')
    store.bootstrap_admin(admin['email'],'Senha1234!')
    other=store.create_user('Outra','other@example.invalid','Senha1234!')
    store.change_access(admin['id'],other['id'],'authorize')
    headers={'Authorization':'Bearer '+store.issue_session(admin['id'])}
    repo=AccountJobRepository(store,admin['id'])
    def save(index,tracking=None):
        return repo.save(JobApplicationObject(application_id=str(uuid4()),job=JobOpportunity(job_id=str(index),title='Analista',company='Empresa',source='Teste'),tracking=tracking))
    with TestClient(main.app) as client:
        assert client.get('/job-applications/metrics').status_code==401
        assert client.get('/job-applications/metrics',headers=headers).json()['total_applications']==0
        first=save(1)
        metrics=client.get('/job-applications/metrics',headers=headers).json()
        assert metrics['total_applications']==1
        assert metrics['interviews']==metrics['hires']==metrics['screening_or_beyond']==0
        save(2,ApplicationTracking(job_id='2',current_status=JobStatus.INTERVIEW))
        metrics=client.get('/job-applications/metrics',headers=headers).json()
        assert metrics['total_applications']==2 and metrics['interviews']==1
        assert metrics['interview_rate']==50.0
        other_headers={'Authorization':'Bearer '+store.issue_session(other['id'])}
        assert client.get('/job-applications/metrics',headers=other_headers).json()['total_applications']==0
        repo.delete(first.application_id)
        metrics=client.get('/job-applications/metrics',headers=headers).json()
        assert metrics['total_applications']==1 and metrics['interview_rate']==100.0

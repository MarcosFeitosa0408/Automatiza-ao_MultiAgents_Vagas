from fastapi.testclient import TestClient
import main
from core.accounts import AccountStore, AccountJobRepository
from core.schemas.application import ApplicationPreparation
from core.schemas.job import JobOpportunity, JobStatus
from core.schemas.job_application import JobApplicationObject
from core.schemas.tracking import ApplicationTracking, TrackingEvent


def test_correction_preserves_history_and_checks_owner_confirmation_and_version(tmp_path, monkeypatch):
    store = AccountStore(str(tmp_path / 'accounts.sqlite3'))
    for module in ('main', 'core.auth_api', 'core.job_correction_api'):
        monkeypatch.setattr(module + '.get_store', lambda: store)
    owner = store.create_user('Pessoa', 'owner@example.invalid', 'Senha1234!')
    store.bootstrap_admin(owner['email'], 'Senha1234!')
    other = store.create_user('Outra', 'other@example.invalid', 'Senha1234!')
    store.change_access(owner['id'], other['id'], 'authorize')
    auth = {'Authorization': 'Bearer ' + store.issue_session(owner['id'])}
    other_auth = {'Authorization': 'Bearer ' + store.issue_session(other['id'])}
    repo = AccountJobRepository(store, owner['id'])
    app = repo.save(JobApplicationObject(application_id='saved', job=JobOpportunity(
        job_id='one', title='Analista', company='Empresa', source='TESTE', requirements=['Parágrafo antigo']),
        tracking=ApplicationTracking(job_id='one', current_status=JobStatus.SCREENING,
            history=[TrackingEvent(status=JobStatus.SCREENING, note='E-mail recebido')], followup_count=1)))
    original_tracking = app.tracking.model_dump(mode='json')
    data = dict(description='Descrição correta', requirements=[' SQL ', 'SQL', 'Power BI'],
                desirable_requirements=[], expected_updated_at=app.updated_at.isoformat(), confirmed=True)
    path = '/job-applications/saved/correct-details'
    with TestClient(main.app) as client:
        assert client.patch(path, json=data).status_code == 401
        assert client.patch(path, json=data, headers=other_auth).status_code == 404
        assert client.patch(path, json={**data, 'confirmed':False}, headers=auth).status_code == 422
        assert repo.get('saved').job.description == app.job.description
        assert client.patch(path, json={**data, 'requirements':['x'*301]}, headers=auth).status_code == 422
        result = client.patch(path, json=data, headers=auth)
        assert result.status_code == 200
        updated = result.json()
        assert updated['tracking'] == original_tracking
        assert updated['job']['requirements'] == ['SQL','Power BI']
        assert updated['job']['job_id'] == app.job.job_id
        assert updated['created_at'] == app.model_dump(mode='json')['created_at']
        assert updated['qualification'] is None and updated['personalization'] is None
        assert client.patch(path, json=data, headers=auth).status_code == 409
        assert len(repo.list_all()) == 1
        prepared = repo.get('saved').model_copy(update={'preparation':ApplicationPreparation(job_id='one', approved_for_human_review=True)})
        repo.save(prepared)
        assert client.patch(path, json={**data,'expected_updated_at':prepared.updated_at.isoformat()}, headers=auth).status_code == 409
        assert repo.get('saved').preparation == prepared.preparation

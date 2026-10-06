import json
import pytest
import httpx
from fastapi import HTTPException
from fastapi.testclient import TestClient
import main
from core import resume_translation as translation
from core.resume_preview import ResumePreview
from core.accounts import AccountStore, AccountJobRepository
from core.schemas.job_application import JobApplicationObject


def preview():
    return ResumePreview(application_id='a', job_title='Cargo', company='Empresa privada', name='Pessoa privada', email='private@example.invalid', phone='11900000000', location='São Paulo', professional_title='Analista', professional_summary='Análise de dados', skills=['SQL'], education=[], experience=[], projects=[], languages={'portuguese': 'Nativo'}, links={'github': 'https://example.invalid'}, ats_keywords=['SQL'], unsupported_requirements=['Outro'], warnings=['Revise'])


def mock_service(monkeypatch, status=200, malformed=False):
    calls = []
    def handle(request):
        body = json.loads(request.content)
        calls.append((request, body))
        return httpx.Response(status, json={'translations': [] if malformed else [{'text': 'translated ' + text} for text in body['text']]})
    original = httpx.Client
    monkeypatch.setattr(translation.httpx, 'Client', lambda **kwargs: original(transport=httpx.MockTransport(handle), **kwargs))
    monkeypatch.setenv('DEEPL_API_KEY', 'fake-key:fx')
    return calls


def test_translation_copies_and_minimizes_fields(monkeypatch):
    calls = mock_service(monkeypatch)
    original = preview()
    before = original.model_dump()
    result = translation.translate_resume(original, 'en-US')
    assert original.model_dump() == before
    assert result.name == original.name and result.email == original.email
    assert result.professional_summary == 'translated Análise de dados'
    assert result.language == 'en-US' and result.ats_keywords == ['SQL']
    request, body = calls[0]
    assert request.url.host == 'api-free.deepl.com'
    assert body['target_lang'] == 'EN-US' and body['source_lang'] == 'PT'
    for excluded in (original.name, original.email, original.phone, original.company, original.links['github']):
        assert excluded not in json.dumps(body)


@pytest.mark.parametrize('status,expected', [(429,429), (456,503), (403,502), (500,502)])
def test_provider_failure_keeps_original_and_hides_details(monkeypatch, status, expected):
    mock_service(monkeypatch, status)
    original = preview()
    with pytest.raises(HTTPException) as error:
        translation.translate_resume(original, 'es')
    assert error.value.status_code == expected
    assert 'fake-key' not in error.value.detail
    assert original.professional_summary == 'Análise de dados'


def test_missing_key_and_oversize_never_send(monkeypatch):
    calls = mock_service(monkeypatch)
    monkeypatch.delenv('DEEPL_API_KEY')
    with pytest.raises(HTTPException) as error:
        translation.translate_resume(preview(), 'es')
    assert error.value.status_code == 503 and not calls
    monkeypatch.setenv('DEEPL_API_KEY', 'fake-key:fx')
    item = preview().model_copy(update={'professional_summary': 'x' * 20001})
    with pytest.raises(HTTPException) as error:
        translation.translate_resume(item, 'es')
    assert error.value.status_code == 413 and not calls


def test_incomplete_provider_response_rejected(monkeypatch):
    mock_service(monkeypatch, malformed=True)
    with pytest.raises(HTTPException) as error:
        translation.translate_resume(preview(), 'es')
    assert error.value.status_code == 502


def test_translation_requires_owner_and_supported_language(tmp_path, monkeypatch):
    store = AccountStore(str(tmp_path / 'accounts.sqlite3'))
    monkeypatch.setattr(main, 'get_store', lambda: store)
    monkeypatch.setattr('core.auth_api.get_store', lambda: store)
    password = 'Senha longa de teste 123!'
    owner = store.create_user('Owner', 'owner@example.invalid', password)
    store.bootstrap_admin(owner['email'], password)
    other = store.create_user('Other', 'other@example.invalid', password)
    store.change_access(owner['id'], other['id'], 'authorize')
    AccountJobRepository(store, owner['id']).save(JobApplicationObject.model_validate({'application_id':'owned', 'job':{'job_id':'job','title':'Analista','company':'Empresa','source':'TEST','requirements':['SQL']}}))
    calls = []
    monkeypatch.setattr(main, 'translate_resume', lambda *args: calls.append(args))
    with TestClient(main.app) as client:
        path = '/job-applications/owned/resume-translation'
        assert client.post(path, json={'language':'es'}).status_code == 401
        header = {'Authorization':'Bearer ' + store.issue_session(other['id'])}
        assert client.post(path, headers=header, json={'language':'es'}).status_code == 404
        assert client.post(path, headers=header, json={'language':'xx'}).status_code == 422
        assert not calls

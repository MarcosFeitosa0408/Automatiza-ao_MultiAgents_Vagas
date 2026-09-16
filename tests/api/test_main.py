from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import main
from core.models import Base
from core.repositories.job_application_repository import (
    InMemoryJobApplicationRepository,
)
from core.repositories.postgres_job_application_repository import (
    PostgreSQLJobApplicationRepository,
)
from main import app


client = TestClient(app)

def test_initialize_configured_database_skips_memory_backend(
    monkeypatch,
):
    calls = []

    monkeypatch.setenv(
        "REPOSITORY_BACKEND",
        "memory",
    )
    monkeypatch.setattr(
        main,
        "initialize_database",
        lambda: calls.append("called"),
    )

    main.initialize_configured_database()

    assert calls == []


def test_initialize_configured_database_runs_for_postgres_backend(
    monkeypatch,
):
    calls = []

    monkeypatch.setenv(
        "REPOSITORY_BACKEND",
        "postgres",
    )
    monkeypatch.setattr(
        main,
        "initialize_database",
        lambda: calls.append("called"),
    )

    main.initialize_configured_database()

    assert calls == ["called"]


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "multiagent-job-platform",
        "version": "0.2.0",
    }


def test_analyze_job():
    payload = {
        "job_id": "teste-api-001",
        "title": "Analista de Dados Júnior",
        "company": "Empresa Teste",
        "source": "API",
        "location": "São Paulo",
        "work_model": "HYBRID",
        "employment_type": "CLT",
        "description": "Vaga para análise de dados e criação de dashboards.",
        "requirements": [
            "Power BI",
            "SQL",
            "Excel",
            "Python",
            "DAX",
        ],
        "desirable_requirements": [],
    }

    response = client.post("/analyze-job", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["job_id"] == "teste-api-001"
    assert data["recommendation"] == "RECOMENDADA"
    assert data["fit_score"] >= 7.0
    assert "power bi" in data["matched_skills"]
    assert "sql" in data["matched_skills"]


def test_personalize_job():
    payload = {
        "job_id": "teste-personalize-001",
        "title": "Analista de Dados Júnior",
        "company": "Empresa Teste",
        "source": "API",
        "location": "São Paulo",
        "work_model": "HYBRID",
        "employment_type": "CLT",
        "description": "Vaga para análise de dados.",
        "requirements": [
            "Power BI",
            "SQL",
            "Python",
            "Excel",
            "DAX",
            "Apache Spark",
        ],
        "desirable_requirements": [],
    }

    response = client.post("/personalize-job", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["qualification"]["job_id"] == "teste-personalize-001"
    assert data["personalization"]["job_id"] == "teste-personalize-001"
    assert data["personalization"]["evidence_verified"] is True

    assert "Power BI" in data["personalization"]["selected_skills"]
    assert "SQL" in data["personalization"]["selected_skills"]

    assert "Apache Spark" not in data["personalization"]["selected_skills"]
    assert "apache spark" in data["personalization"]["unsupported_requirements"]


def test_prepare_application():
    response = client.post(
        "/prepare-application",
        json={
            "job_id": "api-prepare-001",
            "title": "Analista de Dados Júnior",
            "company": "Empresa Teste",
            "source": "API",
            "location": "São Paulo",
            "work_model": "HYBRID",
            "employment_type": "CLT",
            "description": "Vaga para análise de dados.",
            "requirements": [
                "Power BI",
                "SQL",
                "Excel",
                "Python",
                "DAX",
            ],
            "desirable_requirements": [],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["application"]["approved_for_human_review"] is True
    assert data["application"]["decision"] == "PENDING_HUMAN_APPROVAL"
    assert data["application"]["ready_to_apply"] is False


def test_approve_application():
    response = client.post(
        "/approve-application",
        json={
            "application": {
                "job_id": "api-approve-001",
                "approved_for_human_review": True,
                "decision": "PENDING_HUMAN_APPROVAL",
                "ready_to_apply": False,
                "blocking_issues": [],
                "warnings": [],
            }
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["decision"] == "APPROVED_BY_HUMAN"
    assert data["ready_to_apply"] is True


def test_reject_application():
    response = client.post(
        "/reject-application",
        json={
            "application": {
                "job_id": "api-reject-001",
                "approved_for_human_review": True,
                "decision": "PENDING_HUMAN_APPROVAL",
                "ready_to_apply": False,
                "blocking_issues": [],
                "warnings": [],
            }
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["decision"] == "REJECTED_BY_HUMAN"
    assert data["ready_to_apply"] is False


def test_update_tracking_status():
    payload = {
        "tracking": {
            "job_id": "api-tracking-001",
            "current_status": "READY_TO_APPLY",
            "history": [
                {
                    "status": "READY_TO_APPLY",
                    "note": "Acompanhamento da candidatura iniciado.",
                }
            ],
        },
        "new_status": "APPLIED",
        "note": "Candidatura enviada.",
    }

    response = client.post(
        "/update-tracking-status",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["job_id"] == "api-tracking-001"
    assert data["current_status"] == "APPLIED"
    assert len(data["history"]) == 2
    assert data["history"][-1]["status"] == "APPLIED"
    assert data["history"][-1]["note"] == "Candidatura enviada."


def test_create_job_application():
    payload = {
        "application_id": "api-application-001",
        "job": {
            "job_id": "api-job-001",
            "title": "Analista de Dados Júnior",
            "company": "Empresa Teste",
            "source": "API",
            "location": "São Paulo",
            "work_model": "HYBRID",
            "employment_type": "CLT",
            "description": "Vaga para análise de dados.",
            "requirements": [
                "Power BI",
                "SQL",
                "Python",
                "Excel",
            ],
            "desirable_requirements": [],
        },
    }

    response = client.post(
        "/job-applications",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["application_id"] == "api-application-001"
    assert data["job"]["job_id"] == "api-job-001"
    assert data["job"]["title"] == "Analista de Dados Júnior"

    assert data["qualification"] is None
    assert data["personalization"] is None
    assert data["preparation"] is None
    assert data["tracking"] is None

def test_get_job_application():
    create_payload = {
        "application_id": "api-get-001",
        "job": {
            "job_id": "api-get-job-001",
            "title": "Analista de Dados Júnior",
            "company": "Empresa Teste",
            "source": "API",
        },
    }

    create_response = client.post(
        "/job-applications",
        json=create_payload,
    )

    assert create_response.status_code == 200

    response = client.get(
        "/job-applications/api-get-001"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["application_id"] == "api-get-001"
    assert data["job"]["job_id"] == "api-get-job-001"
    assert data["job"]["title"] == "Analista de Dados Júnior"


def test_get_unknown_job_application():
    response = client.get(
        "/job-applications/api-inexistente-001"
    )

    assert response.status_code == 404

    data = response.json()

    assert data["detail"]["message"] == "Candidatura não encontrada."
    assert (
        data["detail"]["application_id"]
        == "api-inexistente-001"
    )


def test_list_job_applications():
    first_payload = {
        "application_id": "api-list-001",
        "job": {
            "job_id": "api-list-job-001",
            "title": "Analista de Dados Júnior",
            "company": "Empresa Teste A",
            "source": "API",
        },
    }

    second_payload = {
        "application_id": "api-list-002",
        "job": {
            "job_id": "api-list-job-002",
            "title": "Analista de BI Júnior",
            "company": "Empresa Teste B",
            "source": "API",
        },
    }

    first_response = client.post(
        "/job-applications",
        json=first_payload,
    )

    second_response = client.post(
        "/job-applications",
        json=second_payload,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    response = client.get("/job-applications")

    assert response.status_code == 200

    data = response.json()

    application_ids = {
        application["application_id"]
        for application in data
    }

    assert "api-list-001" in application_ids
    assert "api-list-002" in application_ids


def test_qualify_stored_job_application():
    create_payload = {
        "application_id": "api-qualify-001",
        "job": {
            "job_id": "api-qualify-job-001",
            "title": "Analista de Dados Júnior",
            "company": "Empresa Teste",
            "source": "API",
            "location": "São Paulo",
            "work_model": "HYBRID",
            "employment_type": "CLT",
            "description": "Vaga para análise de dados.",
            "requirements": [
                "Power BI",
                "SQL",
                "Python",
                "Excel",
                "DAX",
            ],
            "desirable_requirements": [],
        },
    }

    create_response = client.post(
        "/job-applications",
        json=create_payload,
    )

    assert create_response.status_code == 200

    qualify_response = client.post(
        "/job-applications/api-qualify-001/qualify"
    )

    assert qualify_response.status_code == 200

    qualified_data = qualify_response.json()

    assert qualified_data["application_id"] == "api-qualify-001"
    assert qualified_data["qualification"] is not None
    assert qualified_data["qualification"]["job_id"] == "api-qualify-job-001"
    assert qualified_data["qualification"]["fit_score"] >= 7.0

    get_response = client.get(
        "/job-applications/api-qualify-001"
    )

    assert get_response.status_code == 200

    saved_data = get_response.json()

    assert saved_data["qualification"] is not None
    assert saved_data["qualification"]["job_id"] == "api-qualify-job-001"


def test_personalize_stored_job_application():
    create_payload = {
        "application_id": "api-personalize-001",
        "job": {
            "job_id": "api-personalize-job-001",
            "title": "Analista de Dados Júnior",
            "company": "Empresa Teste",
            "source": "API",
            "location": "São Paulo",
            "work_model": "HYBRID",
            "employment_type": "CLT",
            "description": "Vaga para análise de dados.",
            "requirements": [
                "Power BI",
                "SQL",
                "Python",
                "Excel",
                "DAX",
                "Apache Spark",
            ],
            "desirable_requirements": [],
        },
    }

    create_response = client.post(
        "/job-applications",
        json=create_payload,
    )

    assert create_response.status_code == 200

    qualify_response = client.post(
        "/job-applications/api-personalize-001/qualify"
    )

    assert qualify_response.status_code == 200

    personalize_response = client.post(
        "/job-applications/api-personalize-001/personalize"
    )

    assert personalize_response.status_code == 200

    personalized_data = personalize_response.json()

    assert personalized_data["application_id"] == "api-personalize-001"
    assert personalized_data["qualification"] is not None
    assert personalized_data["personalization"] is not None

    assert (
        personalized_data["personalization"]["job_id"]
        == "api-personalize-job-001"
    )

    assert (
        personalized_data["personalization"]["evidence_verified"]
        is True
    )

    assert (
        "Power BI"
        in personalized_data["personalization"]["selected_skills"]
    )

    assert (
        "Apache Spark"
        not in personalized_data["personalization"]["selected_skills"]
    )

    get_response = client.get(
        "/job-applications/api-personalize-001"
    )

    assert get_response.status_code == 200

    saved_data = get_response.json()

    assert saved_data["personalization"] is not None
    assert (
        saved_data["personalization"]["job_id"]
        == "api-personalize-job-001"
    )


def test_prepare_stored_job_application():
    create_payload = {
        "application_id": "api-prepare-stored-001",
        "job": {
            "job_id": "api-prepare-stored-job-001",
            "title": "Analista de Dados Júnior",
            "company": "Empresa Teste",
            "source": "API",
            "location": "São Paulo",
            "work_model": "HYBRID",
            "employment_type": "CLT",
            "description": "Vaga para análise de dados.",
            "requirements": [
                "Power BI",
                "SQL",
                "Python",
                "Excel",
                "DAX",
            ],
            "desirable_requirements": [],
        },
    }

    create_response = client.post(
        "/job-applications",
        json=create_payload,
    )

    assert create_response.status_code == 200

    qualify_response = client.post(
        "/job-applications/api-prepare-stored-001/qualify"
    )

    assert qualify_response.status_code == 200

    personalize_response = client.post(
        "/job-applications/api-prepare-stored-001/personalize"
    )

    assert personalize_response.status_code == 200

    prepare_response = client.post(
        "/job-applications/api-prepare-stored-001/prepare"
    )

    assert prepare_response.status_code == 200

    prepared_data = prepare_response.json()

    assert prepared_data["application_id"] == "api-prepare-stored-001"
    assert prepared_data["qualification"] is not None
    assert prepared_data["personalization"] is not None
    assert prepared_data["preparation"] is not None

    assert (
        prepared_data["preparation"]["decision"]
        == "PENDING_HUMAN_APPROVAL"
    )

    assert (
        prepared_data["preparation"]["ready_to_apply"]
        is False
    )

    get_response = client.get(
        "/job-applications/api-prepare-stored-001"
    )

    assert get_response.status_code == 200

    saved_data = get_response.json()

    assert saved_data["preparation"] is not None
    assert (
        saved_data["preparation"]["decision"]
        == "PENDING_HUMAN_APPROVAL"
    )


def test_approve_stored_job_application():
    create_payload = {
        "application_id": "api-approve-stored-001",
        "job": {
            "job_id": "api-approve-stored-job-001",
            "title": "Analista de Dados Júnior",
            "company": "Empresa Teste",
            "source": "API",
            "location": "São Paulo",
            "work_model": "HYBRID",
            "employment_type": "CLT",
            "description": "Vaga para análise de dados.",
            "requirements": [
                "Power BI",
                "SQL",
                "Python",
                "Excel",
                "DAX",
            ],
            "desirable_requirements": [],
        },
    }

    create_response = client.post(
        "/job-applications",
        json=create_payload,
    )
    assert create_response.status_code == 200

    qualify_response = client.post(
        "/job-applications/api-approve-stored-001/qualify"
    )
    assert qualify_response.status_code == 200

    personalize_response = client.post(
        "/job-applications/api-approve-stored-001/personalize"
    )
    assert personalize_response.status_code == 200

    prepare_response = client.post(
        "/job-applications/api-approve-stored-001/prepare"
    )
    assert prepare_response.status_code == 200

    approve_response = client.post(
        "/job-applications/api-approve-stored-001/approve"
    )

    assert approve_response.status_code == 200

    approved_data = approve_response.json()

    assert (
        approved_data["preparation"]["decision"]
        == "APPROVED_BY_HUMAN"
    )
    assert approved_data["preparation"]["ready_to_apply"] is True

    get_response = client.get(
        "/job-applications/api-approve-stored-001"
    )

    assert get_response.status_code == 200

    saved_data = get_response.json()

    assert (
        saved_data["preparation"]["decision"]
        == "APPROVED_BY_HUMAN"
    )
    assert saved_data["preparation"]["ready_to_apply"] is True


def test_reject_stored_job_application():
    create_payload = {
        "application_id": "api-reject-stored-001",
        "job": {
            "job_id": "api-reject-stored-job-001",
            "title": "Analista de Dados Júnior",
            "company": "Empresa Teste",
            "source": "API",
            "location": "São Paulo",
            "work_model": "HYBRID",
            "employment_type": "CLT",
            "description": "Vaga para análise de dados.",
            "requirements": [
                "Power BI",
                "SQL",
                "Python",
                "Excel",
                "DAX",
            ],
            "desirable_requirements": [],
        },
    }

    create_response = client.post(
        "/job-applications",
        json=create_payload,
    )
    assert create_response.status_code == 200

    qualify_response = client.post(
        "/job-applications/api-reject-stored-001/qualify"
    )
    assert qualify_response.status_code == 200

    personalize_response = client.post(
        "/job-applications/api-reject-stored-001/personalize"
    )
    assert personalize_response.status_code == 200

    prepare_response = client.post(
        "/job-applications/api-reject-stored-001/prepare"
    )
    assert prepare_response.status_code == 200

    reject_response = client.post(
        "/job-applications/api-reject-stored-001/reject"
    )

    assert reject_response.status_code == 200

    rejected_data = reject_response.json()

    assert (
        rejected_data["preparation"]["decision"]
        == "REJECTED_BY_HUMAN"
    )
    assert rejected_data["preparation"]["ready_to_apply"] is False

    get_response = client.get(
        "/job-applications/api-reject-stored-001"
    )

    assert get_response.status_code == 200

    saved_data = get_response.json()

    assert (
        saved_data["preparation"]["decision"]
        == "REJECTED_BY_HUMAN"
    )
    assert saved_data["preparation"]["ready_to_apply"] is False


def test_start_tracking_stored_job_application():
    application_payload = {
    "application_id": "api-tracking-start-001",
    "job": {
        "job_id": "job-tracking-start-001",
        "title": "Analista de Dados Júnior",
        "company": "Empresa Teste",
        "source": "Teste API",
        "location": "São Paulo",
        "work_model": "HYBRID",
        "employment_type": "CLT",
        "description": "Vaga de teste para início de tracking.",
        "requirements": [
            "Power BI",
            "SQL",
            "Python",
            "Excel",
        ],
        "desirable_requirements": [],
    },
}

    create_response = client.post(
        "/job-applications",
        json=application_payload,
    )
    assert create_response.status_code == 200

    qualify_response = client.post(
        "/job-applications/api-tracking-start-001/qualify"
    )
    assert qualify_response.status_code == 200

    personalize_response = client.post(
        "/job-applications/api-tracking-start-001/personalize"
    )
    assert personalize_response.status_code == 200

    prepare_response = client.post(
        "/job-applications/api-tracking-start-001/prepare"
    )
    assert prepare_response.status_code == 200

    approve_response = client.post(
        "/job-applications/api-tracking-start-001/approve"
    )
    assert approve_response.status_code == 200
    assert (
        approve_response.json()["preparation"]["ready_to_apply"]
        is True
    )

    tracking_response = client.post(
        "/job-applications/api-tracking-start-001/tracking/start"
    )

    assert tracking_response.status_code == 200

    tracking_data = tracking_response.json()

    assert tracking_data["tracking"] is not None
    assert (
        tracking_data["tracking"]["job_id"]
        == "job-tracking-start-001"
    )

    stored_response = client.get(
        "/job-applications/api-tracking-start-001"
    )

    assert stored_response.status_code == 200

    stored_data = stored_response.json()

    assert stored_data["tracking"] is not None
    assert (
        stored_data["tracking"]["job_id"]
        == "job-tracking-start-001"
    )


def test_update_tracking_status_stored_job_application():
    application_payload = {
        "application_id": "api-tracking-status-001",
        "job": {
            "job_id": "job-tracking-status-001",
            "title": "Analista de Dados Júnior",
            "company": "Empresa Teste",
            "source": "Teste API",
            "location": "São Paulo",
            "work_model": "HYBRID",
            "employment_type": "CLT",
            "description": "Vaga de teste para atualização de tracking.",
            "requirements": [
                "Power BI",
                "SQL",
                "Python",
                "Excel",
            ],
            "desirable_requirements": [],
        },
    }

    create_response = client.post(
        "/job-applications",
        json=application_payload,
    )
    assert create_response.status_code == 200

    qualify_response = client.post(
        "/job-applications/api-tracking-status-001/qualify"
    )
    assert qualify_response.status_code == 200

    personalize_response = client.post(
        "/job-applications/api-tracking-status-001/personalize"
    )
    assert personalize_response.status_code == 200

    prepare_response = client.post(
        "/job-applications/api-tracking-status-001/prepare"
    )
    assert prepare_response.status_code == 200

    approve_response = client.post(
        "/job-applications/api-tracking-status-001/approve"
    )
    assert approve_response.status_code == 200

    tracking_response = client.post(
        "/job-applications/api-tracking-status-001/tracking/start"
    )
    assert tracking_response.status_code == 200

    status_response = client.post(
        "/job-applications/api-tracking-status-001/tracking/status",
        json={
    "new_status": "APPLIED",
    "note": "Candidatura enviada.",
        },
    )

    assert status_response.status_code == 200

    status_data = status_response.json()

    assert status_data["tracking"] is not None
    assert status_data["tracking"]["current_status"] == "APPLIED"

    stored_response = client.get(
        "/job-applications/api-tracking-status-001"
    )

    assert stored_response.status_code == 200

    stored_data = stored_response.json()

    assert stored_data["tracking"] is not None
    assert stored_data["tracking"]["current_status"] == "APPLIED"


def test_check_follow_up_stored_job_application():
    application_payload = {
        "application_id": "api-follow-up-check-001",
        "job": {
            "job_id": "job-follow-up-check-001",
            "title": "Analista de Dados Júnior",
            "company": "Empresa Teste",
            "source": "Teste API",
            "location": "São Paulo",
            "work_model": "HYBRID",
            "employment_type": "CLT",
            "description": "Vaga de teste para verificação de follow-up.",
            "requirements": [
                "Power BI",
                "SQL",
                "Python",
                "Excel",
            ],
            "desirable_requirements": [],
        },
    }

    create_response = client.post(
        "/job-applications",
        json=application_payload,
    )
    assert create_response.status_code == 200

    qualify_response = client.post(
        "/job-applications/api-follow-up-check-001/qualify"
    )
    assert qualify_response.status_code == 200

    personalize_response = client.post(
        "/job-applications/api-follow-up-check-001/personalize"
    )
    assert personalize_response.status_code == 200

    prepare_response = client.post(
        "/job-applications/api-follow-up-check-001/prepare"
    )
    assert prepare_response.status_code == 200

    approve_response = client.post(
        "/job-applications/api-follow-up-check-001/approve"
    )
    assert approve_response.status_code == 200

    tracking_response = client.post(
        "/job-applications/api-follow-up-check-001/tracking/start"
    )
    assert tracking_response.status_code == 200

    status_response = client.post(
        "/job-applications/api-follow-up-check-001/tracking/status",
        json={
            "new_status": "APPLIED",
            "note": "Candidatura enviada.",
        },
    )
    assert status_response.status_code == 200

    follow_up_response = client.post(
        "/job-applications/api-follow-up-check-001/follow-up/check"
    )

    assert follow_up_response.status_code == 200

    follow_up_data = follow_up_response.json()

    assert (
        follow_up_data["application_id"]
        == "api-follow-up-check-001"
    )
    assert follow_up_data["should_follow_up"] is False
    assert follow_up_data["followup_count"] == 0
    assert follow_up_data["last_followup_at"] is None


def test_register_stored_job_application_follow_up(monkeypatch):
    repository = InMemoryJobApplicationRepository()

    monkeypatch.setattr(
        main.orchestrator,
        "job_application_repository",
        repository,
    )

    application_payload = {
        "application_id": "api-follow-up-register-001",
        "job": {
            "job_id": "job-follow-up-register-001",
            "title": "Analista de Dados Júnior",
            "company": "Empresa Teste",
            "source": "Teste API",
            "location": "São Paulo",
            "work_model": "HYBRID",
            "employment_type": "CLT",
            "description": "Vaga de teste para registro de follow-up.",
            "requirements": [
                "Power BI",
                "SQL",
                "Python",
                "Excel",
            ],
            "desirable_requirements": [],
        },
    }

    create_response = client.post(
        "/job-applications",
        json=application_payload,
    )
    assert create_response.status_code == 200

    qualify_response = client.post(
        "/job-applications/api-follow-up-register-001/qualify"
    )
    assert qualify_response.status_code == 200

    personalize_response = client.post(
        "/job-applications/api-follow-up-register-001/personalize"
    )
    assert personalize_response.status_code == 200

    prepare_response = client.post(
        "/job-applications/api-follow-up-register-001/prepare"
    )
    assert prepare_response.status_code == 200

    approve_response = client.post(
        "/job-applications/api-follow-up-register-001/approve"
    )
    assert approve_response.status_code == 200

    tracking_response = client.post(
        "/job-applications/api-follow-up-register-001/tracking/start"
    )
    assert tracking_response.status_code == 200

    applied_response = client.post(
        "/job-applications/api-follow-up-register-001/tracking/status",
        json={
            "new_status": "APPLIED",
            "note": "Candidatura enviada.",
        },
    )
    assert applied_response.status_code == 200

    first_follow_up_response = client.post(
        "/job-applications/api-follow-up-register-001/follow-up/register"
    )

    assert first_follow_up_response.status_code == 400
    assert first_follow_up_response.json() == {
        "error": "business_rule_violation",
        "message": (
            "Ainda não é o momento permitido para "
            "registrar o follow-up."
        ),
    }

    recovered_response = client.get(
        "/job-applications/api-follow-up-register-001"
    )

    assert recovered_response.status_code == 200

    recovered_application = recovered_response.json()

    assert recovered_application["tracking"]["followup_count"] == 0
    assert (
        recovered_application["tracking"]["last_followup_at"]
        is None
    )


def test_register_follow_up_rejects_invalid_status(monkeypatch):
    repository = InMemoryJobApplicationRepository()

    monkeypatch.setattr(
        main.orchestrator,
        "job_application_repository",
        repository,
    )

    application_payload = {
        "application_id": "api-follow-up-invalid-status-001",
        "job": {
            "job_id": "job-follow-up-invalid-status-001",
            "title": "Analista de Dados Júnior",
            "company": "Empresa Teste",
            "source": "Teste API",
            "location": "São Paulo",
            "work_model": "HYBRID",
            "employment_type": "CLT",
            "description": "Vaga de teste para bloqueio de follow-up.",
            "requirements": [
                "Power BI",
                "SQL",
                "Python",
                "Excel",
            ],
            "desirable_requirements": [],
        },
    }

    create_response = client.post(
        "/job-applications",
        json=application_payload,
    )
    assert create_response.status_code == 200

    qualify_response = client.post(
        "/job-applications/api-follow-up-invalid-status-001/qualify"
    )
    assert qualify_response.status_code == 200

    personalize_response = client.post(
        "/job-applications/api-follow-up-invalid-status-001/personalize"
    )
    assert personalize_response.status_code == 200

    prepare_response = client.post(
        "/job-applications/api-follow-up-invalid-status-001/prepare"
    )
    assert prepare_response.status_code == 200

    approve_response = client.post(
        "/job-applications/api-follow-up-invalid-status-001/approve"
    )
    assert approve_response.status_code == 200

    tracking_response = client.post(
        "/job-applications/api-follow-up-invalid-status-001/tracking/start"
    )
    assert tracking_response.status_code == 200

    follow_up_response = client.post(
        "/job-applications/api-follow-up-invalid-status-001/follow-up/register"
    )

    assert follow_up_response.status_code == 400
    assert follow_up_response.json() == {
        "error": "business_rule_violation",
        "message": (
            "Follow-up só pode ser registrado em candidatura "
            "enviada ou em triagem."
        ),
    }


def test_get_job_application_metrics(monkeypatch):
    repository = InMemoryJobApplicationRepository()

    monkeypatch.setattr(
        main.orchestrator,
        "job_application_repository",
        repository,
    )

    application_payload = {
        "application_id": "api-metrics-001",
        "job": {
            "job_id": "job-metrics-001",
            "title": "Analista de Dados Júnior",
            "company": "Empresa Teste",
            "source": "Teste API",
            "location": "São Paulo",
            "work_model": "HYBRID",
            "employment_type": "CLT",
            "description": "Vaga de teste para métricas do funil.",
            "requirements": [
                "Power BI",
                "SQL",
                "Python",
                "Excel",
            ],
            "desirable_requirements": [],
        },
    }

    create_response = client.post(
        "/job-applications",
        json=application_payload,
    )
    assert create_response.status_code == 200

    qualify_response = client.post(
        "/job-applications/api-metrics-001/qualify"
    )
    assert qualify_response.status_code == 200

    personalize_response = client.post(
        "/job-applications/api-metrics-001/personalize"
    )
    assert personalize_response.status_code == 200

    prepare_response = client.post(
        "/job-applications/api-metrics-001/prepare"
    )
    assert prepare_response.status_code == 200

    approve_response = client.post(
        "/job-applications/api-metrics-001/approve"
    )
    assert approve_response.status_code == 200

    tracking_response = client.post(
        "/job-applications/api-metrics-001/tracking/start"
    )
    assert tracking_response.status_code == 200

    applied_response = client.post(
        "/job-applications/api-metrics-001/tracking/status",
        json={
            "new_status": "APPLIED",
            "note": "Candidatura enviada.",
        },
    )
    assert applied_response.status_code == 200

    screening_response = client.post(
        "/job-applications/api-metrics-001/tracking/status",
        json={
            "new_status": "SCREENING",
            "note": "Candidatura avançou para triagem.",
        },
    )
    assert screening_response.status_code == 200

    metrics_response = client.get(
        "/job-applications/metrics"
    )

    assert metrics_response.status_code == 200

    metrics = metrics_response.json()

    assert metrics["total_applications"] == 1
    assert metrics["screening_or_beyond"] == 1
    assert metrics["interviews"] == 0
    assert metrics["finals"] == 0
    assert metrics["offers"] == 0
    assert metrics["hires"] == 0
    assert metrics["rejections"] == 0

    assert metrics["response_rate"] == 100.0
    assert metrics["interview_rate"] == 0.0
    assert metrics["offer_rate"] == 0.0
    assert metrics["hire_rate"] == 0.0


def test_invalid_tracking_transition_returns_http_400():
    application_payload = {
        "application_id": "api-invalid-transition-001",
        "job": {
            "job_id": "job-invalid-transition-001",
            "title": "Analista de Dados Júnior",
            "company": "Empresa Teste",
            "source": "Teste API",
            "location": "São Paulo",
            "work_model": "HYBRID",
            "employment_type": "CLT",
            "description": "Vaga de teste para validar erro de regra de negócio.",
            "requirements": [
                "Power BI",
                "SQL",
                "Python",
                "Excel",
            ],
            "desirable_requirements": [],
        },
    }

    create_response = client.post(
        "/job-applications",
        json=application_payload,
    )
    assert create_response.status_code == 200

    assert client.post(
        "/job-applications/api-invalid-transition-001/qualify"
    ).status_code == 200

    assert client.post(
        "/job-applications/api-invalid-transition-001/personalize"
    ).status_code == 200

    assert client.post(
        "/job-applications/api-invalid-transition-001/prepare"
    ).status_code == 200

    assert client.post(
        "/job-applications/api-invalid-transition-001/approve"
    ).status_code == 200

    assert client.post(
        "/job-applications/api-invalid-transition-001/tracking/start"
    ).status_code == 200

    invalid_response = client.post(
        "/job-applications/api-invalid-transition-001/tracking/status",
        json={
            "new_status": "SCREENING",
            "note": "Tentativa proposital de transição inválida.",
        },
    )

    assert invalid_response.status_code == 400

    error = invalid_response.json()

    assert error["error"] == "business_rule_violation"
    assert "Transição inválida" in error["message"]


def test_job_application_updated_at_changes_after_update():
    application_payload = {
        "application_id": "api-updated-at-001",
        "job": {
            "job_id": "job-updated-at-001",
            "title": "Analista de Dados Júnior",
            "company": "Empresa Teste",
            "source": "Teste API",
            "location": "São Paulo",
            "work_model": "HYBRID",
            "employment_type": "CLT",
            "description": "Vaga de teste para validar updated_at.",
            "requirements": [
                "Power BI",
                "SQL",
                "Python",
                "Excel",
            ],
            "desirable_requirements": [],
        },
    }

    create_response = client.post(
        "/job-applications",
        json=application_payload,
    )
    assert create_response.status_code == 200

    created_application = create_response.json()

    original_created_at = created_application["created_at"]
    original_updated_at = created_application["updated_at"]

    qualify_response = client.post(
        "/job-applications/api-updated-at-001/qualify"
    )
    assert qualify_response.status_code == 200

    updated_application = qualify_response.json()

    assert updated_application["created_at"] == original_created_at
    assert updated_application["updated_at"] != original_updated_at


def test_api_creates_and_recovers_persisted_job_application(
    monkeypatch,
):
    engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
)

    Base.metadata.create_all(engine)

    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    repository = PostgreSQLJobApplicationRepository(
        session_factory
    )

    monkeypatch.setattr(
        main.orchestrator,
        "job_application_repository",
        repository,
    )

    payload = {
        "application_id": "app-api-persistencia-001",
        "job": {
            "job_id": "vaga-api-persistencia-001",
            "title": "Analista de Dados Júnior",
            "company": "Empresa Teste",
            "source": "TESTE",
            "location": "São Paulo",
            "work_model": "HYBRID",
            "employment_type": "CLT",
            "requirements": [
                "Power BI",
                "SQL",
                "Excel",
                "Python",
            ],
        },
    }

    create_response = client.post(
        "/job-applications",
        json=payload,
    )

    assert create_response.status_code == 200

    get_response = client.get(
        "/job-applications/app-api-persistencia-001"
    )

    assert get_response.status_code == 200

    recovered_application = get_response.json()

    assert (
        recovered_application["application_id"]
        == "app-api-persistencia-001"
    )
    assert (
        recovered_application["job"]["job_id"]
        == "vaga-api-persistencia-001"
    )
    assert (
        recovered_application["job"]["title"]
        == "Analista de Dados Júnior"
    )


def test_api_runs_persisted_application_pipeline(
    monkeypatch,
):
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={
            "check_same_thread": False,
        },
        poolclass=StaticPool,
    )

    Base.metadata.create_all(engine)

    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    repository = PostgreSQLJobApplicationRepository(
        session_factory
    )

    monkeypatch.setattr(
        main.orchestrator,
        "job_application_repository",
        repository,
    )

    application_id = "app-api-pipeline-001"

    payload = {
        "application_id": application_id,
        "job": {
            "job_id": "vaga-api-pipeline-001",
            "title": "Analista de Dados Júnior",
            "company": "Empresa Teste",
            "source": "TESTE",
            "location": "São Paulo",
            "work_model": "HYBRID",
            "employment_type": "CLT",
            "requirements": [
                "Power BI",
                "SQL",
                "Excel",
                "Python",
                "DAX",
            ],
        },
    }

    create_response = client.post(
        "/job-applications",
        json=payload,
    )

    assert create_response.status_code == 200

    qualify_response = client.post(
        f"/job-applications/{application_id}/qualify"
    )

    assert qualify_response.status_code == 200

    personalize_response = client.post(
        f"/job-applications/{application_id}/personalize"
    )

    assert personalize_response.status_code == 200

    prepare_response = client.post(
        f"/job-applications/{application_id}/prepare"
    )

    assert prepare_response.status_code == 200

    approve_response = client.post(
        f"/job-applications/{application_id}/approve"
    )

    assert approve_response.status_code == 200

    tracking_response = client.post(
        f"/job-applications/{application_id}/tracking/start"
    )

    assert tracking_response.status_code == 200

    status_response = client.post(
        f"/job-applications/{application_id}/tracking/status",
        json={
            "new_status": "APPLIED",
            "note": "Candidatura enviada.",
        },
    )

    assert status_response.status_code == 200

    get_response = client.get(
        f"/job-applications/{application_id}"
    )

    assert get_response.status_code == 200

    recovered_application = get_response.json()

    assert recovered_application["application_id"] == application_id
    assert recovered_application["qualification"] is not None
    assert recovered_application["personalization"] is not None
    assert recovered_application["preparation"] is not None
    assert recovered_application["tracking"] is not None

    assert (
        recovered_application["tracking"]["current_status"]
        == "APPLIED"
    )

    assert (
        recovered_application["tracking"]["history"][-1]["note"]
        == "Candidatura enviada."
    )


def test_delete_stored_job_application():
    application_id = "app-delete-api-001"

    payload = {
        "application_id": application_id,
        "job": {
            "job_id": "vaga-delete-api-001",
            "title": "Analista de Dados Júnior",
            "company": "Empresa Teste",
            "source": "TESTE",
            "location": "São Paulo",
            "work_model": "HYBRID",
            "employment_type": "CLT",
            "requirements": [
                "Power BI",
                "SQL",
                "Excel",
                "Python",
            ],
        },
    }

    create_response = client.post(
        "/job-applications",
        json=payload,
    )

    assert create_response.status_code == 200

    delete_response = client.delete(
        f"/job-applications/{application_id}"
    )

    assert delete_response.status_code == 200
    assert delete_response.json() == {
        "application_id": application_id,
        "deleted": True,
    }

    get_response = client.get(
        f"/job-applications/{application_id}"
    )

    assert get_response.status_code == 404


def test_delete_missing_job_application_returns_404():
    response = client.delete(
        "/job-applications/app-delete-inexistente"
    )

    assert response.status_code == 404

    assert response.json()["detail"] == {
        "message": "Candidatura não encontrada.",
        "application_id": "app-delete-inexistente",
    }





import pytest
from fastapi.testclient import TestClient

import main
from agents.agent_00_memory.memory_agent import MemoryAgent
from core.schemas.candidate import MasterProfile
from core.schemas.job import JobOpportunity
from core.schemas.job_application import JobApplicationObject


@pytest.fixture
def resume_context(monkeypatch):
    data = MemoryAgent("tests/fixtures/profile.json").load_profile().model_dump(mode="json")

    data["candidate"]["name"] = "Pessoa de Teste"
    data["candidate"]["email"] = "pessoa@example.com"
    data["candidate"]["phone"] = "11900000000"
    data["professional_positioning"]["summary"] = "Análise de dados e relatórios."

    data["skills"] = {
        "core": ["SQL", "Power BI"],
        "database": [],
        "python": [],
        "analytics": [],
        "tools": [],
        "automation": [],
    }

    data["projects"] = [
        {
            "name": "Projeto Público",
            "description": "Dashboard de vendas.",
            "technologies": ["Power BI"],
            "authorized_for_portfolio": True,
        },
        {
            "name": "Projeto Restrito",
            "description": "Projeto não autorizado.",
            "technologies": ["Power BI"],
            "authorized_for_portfolio": False,
        },
    ]

    profile = MasterProfile.model_validate(data)

    application = JobApplicationObject(
        application_id="resume-test",
        job=JobOpportunity(
            job_id="job-resume-test",
            title="Analista de Dados",
            company="Empresa de Teste",
            source="TESTE",
            requirements=["SQL", "Power BI", "Kubernetes"],
        ),
    )

    monkeypatch.setattr(
        main.orchestrator.memory_agent,
        "get_profile",
        lambda: profile,
    )

    monkeypatch.setattr(
        main.orchestrator,
        "get_job_application",
        lambda application_id: (
            application if application_id == "resume-test" else None
        ),
    )

    with TestClient(main.app) as client:
        yield client, profile, application


def test_preview_uses_profile_and_excludes_unsupported_skills(resume_context):
    client, profile, application = resume_context
    previous_application = application.model_dump(mode="json")

    response = client.post("/job-applications/resume-test/resume-preview")

    assert response.status_code == 200
    result = response.json()

    assert result["name"] == "Pessoa de Teste"
    assert result["email"] == "pessoa@example.com"
    assert set(result["skills"]) == {"SQL", "Power BI"}
    assert "Kubernetes" not in result["skills"]
    assert "kubernetes" in {
        item.lower() for item in result["unsupported_requirements"]
    }

    assert result["education"] == [
        item.model_dump(mode="json") for item in profile.education
    ]

    # Gerar uma prévia não muda aprovação ou acompanhamento.
    assert application.model_dump(mode="json") == previous_application


def test_preview_excludes_projects_without_authorization(resume_context):
    client, profile, application = resume_context

    response = client.post("/job-applications/resume-test/resume-preview")

    assert response.status_code == 200
    assert [
        project["name"] for project in response.json()["projects"]
    ] == ["Projeto Público"]


def test_preview_requires_informed_job_requirements(resume_context):
    client, profile, application = resume_context
    application.job.requirements = []

    response = client.post("/job-applications/resume-test/resume-preview")

    assert response.status_code == 400
    assert "requisitos" in response.json()["message"].lower()


def test_preview_returns_404_for_missing_application(resume_context):
    client, profile, application = resume_context

    response = client.post("/job-applications/missing/resume-preview")

    assert response.status_code == 404
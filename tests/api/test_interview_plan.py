import pytest
from fastapi.testclient import TestClient

import main
from agents.agent_00_memory.memory_agent import MemoryAgent
from core.schemas.job import JobOpportunity
from core.schemas.job_application import JobApplicationObject


@pytest.fixture
def interview_context(monkeypatch):
    profile = MemoryAgent("tests/fixtures/profile.json").load_profile()

    application = JobApplicationObject(
        application_id="interview-test",
        job=JobOpportunity(
            job_id="job-interview-test",
            title="Analista de Dados",
            company="Empresa Teste",
            source="TESTE",
            requirements=["SQL", "Power BI", "SQL"],
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
            application if application_id == "interview-test" else None
        ),
    )

    with TestClient(main.app) as client:
        yield client, profile, application


def test_interview_plan_uses_job_requirements_without_duplicates(
    interview_context,
):
    client, profile, application = interview_context

    response = client.post(
        "/job-applications/interview-test/interview-plan"
    )

    assert response.status_code == 200
    plan = response.json()

    assert plan["job_title"] == "Analista de Dados"
    assert plan["company"] == "Empresa Teste"

    technical = [
        item for item in plan["questions"]
        if item["category"] == "Técnica"
    ]

    assert len(technical) == 2
    assert "SQL" in technical[0]["question"]
    assert "Power BI" in technical[1]["question"]

    question_ids = [item["question_id"] for item in plan["questions"]]
    assert len(question_ids) == len(set(question_ids))


def test_interview_plan_does_not_change_profile_or_application(
    interview_context,
):
    client, profile, application = interview_context
    previous_profile = profile.model_dump(mode="json")
    previous_application = application.model_dump(mode="json")

    response = client.post(
        "/job-applications/interview-test/interview-plan"
    )

    assert response.status_code == 200
    assert profile.model_dump(mode="json") == previous_profile
    assert application.model_dump(mode="json") == previous_application


@pytest.mark.parametrize("requirements", [[], ["", "   "]])
def test_interview_plan_requires_informed_requirements(
    interview_context,
    requirements,
):
    client, profile, application = interview_context
    application.job.requirements = requirements

    response = client.post(
        "/job-applications/interview-test/interview-plan"
    )

    assert response.status_code == 400
    assert "requisitos" in response.json()["message"].lower()


def test_interview_plan_returns_404_for_missing_application(
    interview_context,
):
    client, profile, application = interview_context

    response = client.post(
        "/job-applications/missing/interview-plan"
    )

    assert response.status_code == 404


def test_interview_plan_returns_404_for_missing_profile(
    interview_context,
    monkeypatch,
):
    client, profile, application = interview_context

    def missing_profile():
        raise FileNotFoundError("Perfil não encontrado")

    monkeypatch.setattr(
        main.orchestrator.memory_agent,
        "get_profile",
        missing_profile,
    )

    response = client.post(
        "/job-applications/interview-test/interview-plan"
    )

    assert response.status_code == 404
    assert "perfil" in response.json()["detail"].lower()

from core.repositories.job_application_repository import (
    InMemoryJobApplicationRepository,
)
from core.schemas.job import JobOpportunity
from core.schemas.job_application import JobApplicationObject


def build_application(
    application_id: str,
    job_id: str,
) -> JobApplicationObject:
    job = JobOpportunity(
        job_id=job_id,
        title="Analista de Dados Júnior",
        company="Empresa Teste",
        source="TESTE",
    )

    return JobApplicationObject(
        application_id=application_id,
        job=job,
    )


def test_repository_saves_and_gets_application():
    repository = InMemoryJobApplicationRepository()

    application = build_application(
        application_id="repository-001",
        job_id="job-repository-001",
    )

    repository.save(application)

    saved = repository.get("repository-001")

    assert saved is not None
    assert saved.application_id == "repository-001"
    assert saved.job.job_id == "job-repository-001"


def test_repository_lists_all_applications():
    repository = InMemoryJobApplicationRepository()

    repository.save(
        build_application(
            application_id="repository-002",
            job_id="job-repository-002",
        )
    )

    repository.save(
        build_application(
            application_id="repository-003",
            job_id="job-repository-003",
        )
    )

    applications = repository.list_all()

    assert len(applications) == 2


def test_repository_updates_existing_application():
    repository = InMemoryJobApplicationRepository()

    application = build_application(
        application_id="repository-004",
        job_id="job-repository-004",
    )

    repository.save(application)

    updated = application.model_copy(
        update={
            "qualification": None,
        }
    )

    repository.save(updated)

    applications = repository.list_all()

    assert len(applications) == 1
    assert repository.get("repository-004") is not None


def test_repository_deletes_application():
    repository = InMemoryJobApplicationRepository()

    application = build_application(
        application_id="repository-005",
        job_id="job-repository-005",
    )

    repository.save(application)

    deleted = repository.delete("repository-005")

    assert deleted is True
    assert repository.get("repository-005") is None
    assert repository.list_all() == []


def test_repository_returns_false_when_deleting_unknown_application():
    repository = InMemoryJobApplicationRepository()

    deleted = repository.delete("repository-inexistente")

    assert deleted is False

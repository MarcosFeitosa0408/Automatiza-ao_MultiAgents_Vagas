from core.orchestrator.orchestrator import JobOrchestrator
from core.repositories.job_application_repository import (
    InMemoryJobApplicationRepository,
)
from core.repositories.postgres_job_application_repository import (
    PostgreSQLJobApplicationRepository,
)


def test_orchestrator_uses_memory_repository_by_default(
    monkeypatch,
):
    monkeypatch.delenv(
        "REPOSITORY_BACKEND",
        raising=False,
    )

    orchestrator = JobOrchestrator()

    assert isinstance(
        orchestrator.job_application_repository,
        InMemoryJobApplicationRepository,
    )


def test_orchestrator_uses_postgres_repository_when_configured(
    monkeypatch,
):
    monkeypatch.setenv(
        "REPOSITORY_BACKEND",
        "postgres",
    )
    monkeypatch.setenv(
        "DATABASE_URL",
        "sqlite+pysqlite:///:memory:",
    )

    orchestrator = JobOrchestrator()

    assert isinstance(
        orchestrator.job_application_repository,
        PostgreSQLJobApplicationRepository,
    )

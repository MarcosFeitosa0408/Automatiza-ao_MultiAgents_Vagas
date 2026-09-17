import pytest

from core.repositories.factory import (
    create_job_application_repository,
)
from core.repositories.job_application_repository import (
    InMemoryJobApplicationRepository,
)
from core.repositories.postgres_job_application_repository import (
    PostgreSQLJobApplicationRepository,
)


def test_factory_uses_memory_by_default(
    monkeypatch,
):
    monkeypatch.delenv(
        "REPOSITORY_BACKEND",
        raising=False,
    )

    repository = create_job_application_repository()

    assert isinstance(
        repository,
        InMemoryJobApplicationRepository,
    )


def test_factory_uses_postgres_when_configured(
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

    repository = create_job_application_repository()

    assert isinstance(
        repository,
        PostgreSQLJobApplicationRepository,
    )


def test_factory_rejects_invalid_backend(
    monkeypatch,
):
    monkeypatch.setenv(
        "REPOSITORY_BACKEND",
        "invalid",
    )

    with pytest.raises(
        ValueError,
        match="REPOSITORY_BACKEND inválido",
    ):
        create_job_application_repository()

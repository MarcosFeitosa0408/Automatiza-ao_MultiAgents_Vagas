import os

from core.database import create_session_factory
from core.repositories.base_job_application_repository import (
    BaseJobApplicationRepository,
)
from core.repositories.job_application_repository import (
    InMemoryJobApplicationRepository,
)
from core.repositories.postgres_job_application_repository import (
    PostgreSQLJobApplicationRepository,
)


def create_job_application_repository(
) -> BaseJobApplicationRepository:
    """Cria o repository conforme o backend configurado."""

    backend = os.getenv(
        "REPOSITORY_BACKEND",
        "memory",
    ).lower()

    if backend == "memory":
        return InMemoryJobApplicationRepository()

    if backend == "postgres":
        session_factory = create_session_factory()

        return PostgreSQLJobApplicationRepository(
            session_factory
        )

    raise ValueError(
        f"REPOSITORY_BACKEND inválido: {backend}"
    )

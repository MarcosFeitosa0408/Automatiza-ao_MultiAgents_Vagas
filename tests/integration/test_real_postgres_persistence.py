import os

import pytest

from core.database import (
    create_database_engine,
    create_session_factory,
)
from core.models import Base
from core.orchestrator.orchestrator import JobOrchestrator
from core.repositories.postgres_job_application_repository import (
    PostgreSQLJobApplicationRepository,
)
from core.schemas.job import JobOpportunity, JobStatus, WorkModel
from core.schemas.job_application import JobApplicationObject


def test_real_postgres_persists_job_application():
    database_url = os.getenv("DATABASE_URL")

    if not database_url or not database_url.startswith(
        "postgresql"
    ):
        pytest.skip(
            "PostgreSQL real não configurado para este ambiente."
        )

    engine = create_database_engine()

    Base.metadata.create_all(engine)

    session_factory = create_session_factory()

    repository = PostgreSQLJobApplicationRepository(
        session_factory
    )

    application = JobApplicationObject(
        application_id="app-real-postgres-001",
        job=JobOpportunity(
            job_id="vaga-real-postgres-001",
            title="Analista de Dados Júnior",
            company="Empresa Teste PostgreSQL",
            source="TESTE",
            location="São Paulo",
            work_model=WorkModel.HYBRID,
            employment_type="CLT",
            requirements=[
                "Power BI",
                "SQL",
                "Python",
                "Excel",
            ],
        ),
    )

    repository.save(application)

    recovered_application = repository.get(
        "app-real-postgres-001"
    )

    assert recovered_application is not None
    assert (
        recovered_application.application_id
        == "app-real-postgres-001"
    )
    assert (
        recovered_application.job.job_id
        == "vaga-real-postgres-001"
    )
    assert (
        recovered_application.job.title
        == "Analista de Dados Júnior"
    )

    repository.delete(
        "app-real-postgres-001"
    )

    engine.dispose()


def test_real_postgres_runs_complete_application_pipeline():
    database_url = os.getenv("DATABASE_URL")
    repository_backend = os.getenv("REPOSITORY_BACKEND")

    if (
        not database_url
        or not database_url.startswith("postgresql")
        or repository_backend != "postgres"
    ):
        pytest.skip(
            "Backend PostgreSQL real não configurado para este ambiente."
        )

    engine = create_database_engine()

    Base.metadata.create_all(engine)

    orchestrator = JobOrchestrator()

    assert isinstance(
        orchestrator.job_application_repository,
        PostgreSQLJobApplicationRepository,
    )

    application_id = "app-real-postgres-pipeline-001"

    job = JobOpportunity(
        job_id="vaga-real-postgres-pipeline-001",
        title="Analista de Dados Júnior",
        company="Empresa Teste PostgreSQL",
        source="TESTE",
        location="São Paulo",
        work_model=WorkModel.HYBRID,
        employment_type="CLT",
        requirements=[
            "Power BI",
            "SQL",
            "Python",
            "Excel",
            "DAX",
        ],
    )

    application = orchestrator.create_job_application(
        job=job,
        application_id=application_id,
    )

    application = orchestrator.qualify_job_application(
        application
    )

    application = orchestrator.personalize_job_application(
        application
    )

    application = orchestrator.prepare_job_application(
        application
    )

    application = orchestrator.approve_job_application(
        application
    )

    application = orchestrator.start_job_application_tracking(
        application
    )

    application = orchestrator.update_job_application_status(
        application,
        JobStatus.APPLIED,
        "Candidatura enviada.",
    )

    orchestrator.save_job_application(
        application
    )

    recovered_application = (
        orchestrator.get_job_application(
            application_id
        )
    )

    assert recovered_application is not None
    assert (
        recovered_application.application_id
        == application_id
    )
    assert recovered_application.qualification is not None
    assert recovered_application.personalization is not None
    assert recovered_application.preparation is not None
    assert recovered_application.tracking is not None
    assert (
        recovered_application.tracking.current_status
        == JobStatus.APPLIED
    )
    assert (
        recovered_application.tracking.history[-1].note
        == "Candidatura enviada."
    )

    orchestrator.job_application_repository.delete(
        application_id
    )

    engine.dispose()

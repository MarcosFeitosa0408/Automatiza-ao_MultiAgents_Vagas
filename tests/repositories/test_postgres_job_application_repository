from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.models import Base
from core.repositories.postgres_job_application_repository import (
    PostgreSQLJobApplicationRepository,
)
from core.schemas.job import JobOpportunity
from core.schemas.job_application import JobApplicationObject


def create_repository():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
    )

    Base.metadata.create_all(engine)

    session_factory = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    return PostgreSQLJobApplicationRepository(
        session_factory
    )


def create_application(
    application_id: str = "repository-postgres-001",
) -> JobApplicationObject:
    job = JobOpportunity(
        job_id="job-postgres-001",
        title="Analista de Dados Júnior",
        company="Empresa Teste",
        source="Teste Repository",
        location="São Paulo",
        work_model="HYBRID",
        employment_type="CLT",
        description="Vaga de teste para persistência.",
        requirements=[
            "Power BI",
            "SQL",
            "Python",
            "Excel",
        ],
        desirable_requirements=[],
    )

    return JobApplicationObject(
        application_id=application_id,
        job=job,
    )


def test_save_and_get_job_application():
    repository = create_repository()
    application = create_application()

    repository.save(application)

    stored_application = repository.get(
        application.application_id
    )

    assert stored_application is not None
    assert stored_application.application_id == application.application_id
    assert stored_application.job.job_id == application.job.job_id


def test_list_all_job_applications():
    repository = create_repository()

    first_application = create_application(
        "repository-postgres-list-001"
    )
    second_application = create_application(
        "repository-postgres-list-002"
    )

    repository.save(first_application)
    repository.save(second_application)

    applications = repository.list_all()

    assert len(applications) == 2


def test_delete_job_application():
    repository = create_repository()
    application = create_application(
        "repository-postgres-delete-001"
    )

    repository.save(application)

    deleted = repository.delete(
        application.application_id
    )

    assert deleted is True
    assert repository.get(
        application.application_id
    ) is None

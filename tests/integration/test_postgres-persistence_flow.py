from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.models import Base
from core.orchestrator.orchestrator import JobOrchestrator
from core.repositories.postgres_job_application_repository import (
    PostgreSQLJobApplicationRepository,
)
from core.schemas.job import JobOpportunity, JobStatus, WorkModel


def test_orchestrator_persists_and_recovers_job_application():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
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

    orchestrator = JobOrchestrator()
    orchestrator.job_application_repository = repository

    job = JobOpportunity(
        job_id="vaga-persistencia-001",
        title="Analista de Dados Júnior",
        company="Empresa Teste",
        source="TESTE",
        location="São Paulo",
        work_model=WorkModel.HYBRID,
        employment_type="CLT",
        requirements=[
            "Power BI",
            "SQL",
            "Excel",
            "Python",
        ],
    )

    application = orchestrator.create_job_application(
        job=job,
        application_id="app-persistencia-001",
    )

    orchestrator.save_job_application(application)

    recovered_application = (
        orchestrator.job_application_repository.get(
            "app-persistencia-001"
        )
    )

    assert recovered_application is not None
    assert (
        recovered_application.application_id
        == "app-persistencia-001"
    )
    assert recovered_application.job.job_id == "vaga-persistencia-001"
    assert recovered_application.job.title == "Analista de Dados Júnior"


def test_orchestrator_updates_persisted_job_application():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
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

    orchestrator = JobOrchestrator()
    orchestrator.job_application_repository = repository

    job = JobOpportunity(
        job_id="vaga-persistencia-002",
        title="Analista de Dados Júnior",
        company="Empresa Teste",
        source="TESTE",
        location="São Paulo",
        work_model=WorkModel.HYBRID,
        employment_type="CLT",
        requirements=[
            "Power BI",
            "SQL",
            "Python",
        ],
    )

    application = orchestrator.create_job_application(
        job=job,
        application_id="app-persistencia-002",
    )

    orchestrator.save_job_application(application)

    updated_application = application.model_copy(
        update={
            "job": job.model_copy(
                update={
                    "title": "Analista de BI Júnior",
                }
            )
        }
    )

    orchestrator.save_job_application(
        updated_application
    )

    recovered_application = repository.get(
        "app-persistencia-002"
    )

    applications = repository.list_all()

    assert recovered_application is not None
    assert (
        recovered_application.job.title
        == "Analista de BI Júnior"
    )
    assert len(applications) == 1


def test_orchestrator_deletes_persisted_job_application():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
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

    orchestrator = JobOrchestrator()
    orchestrator.job_application_repository = repository

    job = JobOpportunity(
        job_id="vaga-persistencia-003",
        title="Analista de Dados Júnior",
        company="Empresa Teste",
        source="TESTE",
        location="São Paulo",
        work_model=WorkModel.HYBRID,
        employment_type="CLT",
        requirements=[
            "Power BI",
            "SQL",
        ],
    )

    application = orchestrator.create_job_application(
        job=job,
        application_id="app-persistencia-003",
    )

    orchestrator.save_job_application(application)

    deleted = repository.delete(
        "app-persistencia-003"
    )

    recovered_application = repository.get(
        "app-persistencia-003"
    )

    assert deleted is True
    assert recovered_application is None


def test_qualification_is_preserved_after_persistence():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
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

    orchestrator = JobOrchestrator()
    orchestrator.job_application_repository = repository

    job = JobOpportunity(
        job_id="vaga-persistencia-004",
        title="Analista de Dados Júnior",
        company="Empresa Teste",
        source="TESTE",
        location="São Paulo",
        work_model=WorkModel.HYBRID,
        employment_type="CLT",
        requirements=[
            "Power BI",
            "SQL",
            "Excel",
            "Python",
            "DAX",
        ],
    )

    application = orchestrator.create_job_application(
        job=job,
        application_id="app-persistencia-004",
    )

    qualified_application = (
        orchestrator.qualify_job_application(
            application
        )
    )

    orchestrator.save_job_application(
        qualified_application
    )

    recovered_application = repository.get(
        "app-persistencia-004"
    )

    assert recovered_application is not None
    assert recovered_application.qualification is not None
    assert (
        recovered_application.qualification.fit_score
        == qualified_application.qualification.fit_score
    )
    assert (
        recovered_application.qualification.recommendation
        == qualified_application.qualification.recommendation
    )


def test_personalization_is_preserved_after_persistence():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
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

    orchestrator = JobOrchestrator()
    orchestrator.job_application_repository = repository

    job = JobOpportunity(
        job_id="vaga-persistencia-005",
        title="Analista de Dados Júnior",
        company="Empresa Teste",
        source="TESTE",
        location="São Paulo",
        work_model=WorkModel.HYBRID,
        employment_type="CLT",
        requirements=[
            "Power BI",
            "SQL",
            "Excel",
            "Python",
            "DAX",
        ],
    )

    application = orchestrator.create_job_application(
        job=job,
        application_id="app-persistencia-005",
    )

    qualified_application = (
        orchestrator.qualify_job_application(
            application
        )
    )

    personalized_application = (
        orchestrator.personalize_job_application(
            qualified_application
        )
    )

    orchestrator.save_job_application(
        personalized_application
    )

    recovered_application = repository.get(
        "app-persistencia-005"
    )

    assert recovered_application is not None
    assert recovered_application.qualification is not None
    assert recovered_application.personalization is not None
    assert (
        recovered_application.personalization
        == personalized_application.personalization
    )


def test_human_approval_is_preserved_after_persistence():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
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

    orchestrator = JobOrchestrator()
    orchestrator.job_application_repository = repository

    job = JobOpportunity(
        job_id="vaga-persistencia-006",
        title="Analista de Dados Júnior",
        company="Empresa Teste",
        source="TESTE",
        location="São Paulo",
        work_model=WorkModel.HYBRID,
        employment_type="CLT",
        requirements=[
            "Power BI",
            "SQL",
            "Excel",
            "Python",
            "DAX",
        ],
    )

    application = orchestrator.create_job_application(
        job=job,
        application_id="app-persistencia-006",
    )

    qualified_application = (
        orchestrator.qualify_job_application(
            application
        )
    )

    personalized_application = (
        orchestrator.personalize_job_application(
            qualified_application
        )
    )

    prepared_application = (
        orchestrator.prepare_job_application(
            personalized_application
        )
    )

    approved_application = (
        orchestrator.approve_job_application(
            prepared_application
        )
    )

    orchestrator.save_job_application(
        approved_application
    )

    recovered_application = repository.get(
        "app-persistencia-006"
    )

    assert recovered_application is not None
    assert recovered_application.preparation is not None
    assert (
        recovered_application.preparation
        == approved_application.preparation
    )


def test_human_rejection_is_preserved_after_persistence():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
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

    orchestrator = JobOrchestrator()
    orchestrator.job_application_repository = repository

    job = JobOpportunity(
        job_id="vaga-persistencia-007",
        title="Analista de Dados Júnior",
        company="Empresa Teste",
        source="TESTE",
        location="São Paulo",
        work_model=WorkModel.HYBRID,
        employment_type="CLT",
        requirements=[
            "Power BI",
            "SQL",
            "Excel",
            "Python",
            "DAX",
        ],
    )

    application = orchestrator.create_job_application(
        job=job,
        application_id="app-persistencia-007",
    )

    qualified_application = (
        orchestrator.qualify_job_application(
            application
        )
    )

    personalized_application = (
        orchestrator.personalize_job_application(
            qualified_application
        )
    )

    prepared_application = (
        orchestrator.prepare_job_application(
            personalized_application
        )
    )

    rejected_application = (
        orchestrator.reject_job_application(
            prepared_application
        )
    )

    orchestrator.save_job_application(
        rejected_application
    )

    recovered_application = repository.get(
        "app-persistencia-007"
    )

    assert recovered_application is not None
    assert recovered_application.preparation is not None
    assert (
        recovered_application.preparation
        == rejected_application.preparation
    )


def test_tracking_status_is_preserved_after_persistence():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
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

    orchestrator = JobOrchestrator()
    orchestrator.job_application_repository = repository

    job = JobOpportunity(
        job_id="vaga-persistencia-008",
        title="Analista de Dados Júnior",
        company="Empresa Teste",
        source="TESTE",
        location="São Paulo",
        work_model=WorkModel.HYBRID,
        employment_type="CLT",
        requirements=[
            "Power BI",
            "SQL",
            "Excel",
            "Python",
            "DAX",
        ],
    )

    application = orchestrator.create_job_application(
        job=job,
        application_id="app-persistencia-008",
    )

    qualified_application = (
        orchestrator.qualify_job_application(
            application
        )
    )

    personalized_application = (
        orchestrator.personalize_job_application(
            qualified_application
        )
    )

    prepared_application = (
        orchestrator.prepare_job_application(
            personalized_application
        )
    )

    approved_application = (
        orchestrator.approve_job_application(
            prepared_application
        )
    )

    tracked_application = (
        orchestrator.start_job_application_tracking(
            approved_application
        )
    )

    applied_application = (
        orchestrator.update_job_application_status(
            tracked_application,
            JobStatus.APPLIED,
            "Candidatura enviada.",
        )
    )

    orchestrator.save_job_application(
        applied_application
    )

    recovered_application = repository.get(
        "app-persistencia-008"
    )

    assert recovered_application is not None
    assert recovered_application.tracking is not None
    assert (
        recovered_application.tracking.current_status
        == JobStatus.APPLIED
    )
    assert len(recovered_application.tracking.history) == 2
    assert (
        recovered_application.tracking.history[-1].note
        == "Candidatura enviada."
    )


def test_recovered_application_remains_eligible_for_follow_up():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
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

    orchestrator = JobOrchestrator()
    orchestrator.job_application_repository = repository

    job = JobOpportunity(
        job_id="vaga-persistencia-009",
        title="Analista de Dados Júnior",
        company="Empresa Teste",
        source="TESTE",
        location="São Paulo",
        work_model=WorkModel.HYBRID,
        employment_type="CLT",
        requirements=[
            "Power BI",
            "SQL",
            "Excel",
            "Python",
            "DAX",
        ],
    )

    application = orchestrator.create_job_application(
        job=job,
        application_id="app-persistencia-009",
    )

    qualified_application = (
        orchestrator.qualify_job_application(
            application
        )
    )

    personalized_application = (
        orchestrator.personalize_job_application(
            qualified_application
        )
    )

    prepared_application = (
        orchestrator.prepare_job_application(
            personalized_application
        )
    )

    approved_application = (
        orchestrator.approve_job_application(
            prepared_application
        )
    )

    tracked_application = (
        orchestrator.start_job_application_tracking(
            approved_application
        )
    )

    applied_application = (
        orchestrator.update_job_application_status(
            tracked_application,
            JobStatus.APPLIED,
            "Candidatura enviada.",
        )
    )

    orchestrator.save_job_application(
        applied_application
    )

    recovered_application = repository.get(
        "app-persistencia-009"
    )

    assert recovered_application is not None
    assert recovered_application.tracking is not None

    applied_events = [
        event
        for event in recovered_application.tracking.history
        if event.status == JobStatus.APPLIED
    ]

    assert applied_events

    applied_at = applied_events[-1].occurred_at

    now = applied_at + timedelta(
        days=5
    )

    should_follow_up = (
        orchestrator.should_follow_up_job_application(
            recovered_application,
            now=now,
        )
    )

    assert should_follow_up is True


def test_metrics_are_calculated_from_persisted_applications():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
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

    orchestrator = JobOrchestrator()
    orchestrator.job_application_repository = repository

    for index in range(2):
        job = JobOpportunity(
            job_id=f"vaga-metricas-{index}",
            title="Analista de Dados Júnior",
            company="Empresa Teste",
            source="TESTE",
            location="São Paulo",
            work_model=WorkModel.HYBRID,
            employment_type="CLT",
            requirements=[
                "Power BI",
                "SQL",
                "Excel",
                "Python",
                "DAX",
            ],
        )

        application = orchestrator.create_job_application(
            job=job,
            application_id=f"app-metricas-{index}",
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

        if index == 0:
            application = orchestrator.update_job_application_status(
                application,
                JobStatus.SCREENING,
                "Candidatura em triagem.",
            )

        orchestrator.save_job_application(
            application
        )

    persisted_applications = repository.list_all()

    metrics = orchestrator.calculate_job_application_metrics(
        persisted_applications
    )

    assert metrics["total_applications"] == 2
    assert metrics["screening_or_beyond"] == 1
    assert metrics["interviews"] == 0
    assert metrics["finals"] == 0
    assert metrics["offers"] == 0
    assert metrics["hires"] == 0
    assert metrics["rejections"] == 0
    assert metrics["response_rate"] == 50.0
    assert metrics["interview_rate"] == 0.0
    assert metrics["offer_rate"] == 0.0
    assert metrics["hire_rate"] == 0.0


def test_follow_up_respects_first_and_second_waiting_periods():
    orchestrator = JobOrchestrator()

    job = JobOpportunity(
        job_id="vaga-follow-up-timing-010",
        title="Analista de Dados Júnior",
        company="Empresa Teste",
        source="TESTE",
        location="São Paulo",
        work_model=WorkModel.HYBRID,
        employment_type="CLT",
        requirements=[
            "Power BI",
            "SQL",
            "Excel",
            "Python",
            "DAX",
        ],
    )

    application = orchestrator.create_job_application(
        job=job,
        application_id="app-follow-up-timing-010",
    )

    qualified_application = (
        orchestrator.qualify_job_application(
            application
        )
    )

    personalized_application = (
        orchestrator.personalize_job_application(
            qualified_application
        )
    )

    prepared_application = (
        orchestrator.prepare_job_application(
            personalized_application
        )
    )

    approved_application = (
        orchestrator.approve_job_application(
            prepared_application
        )
    )

    tracked_application = (
        orchestrator.start_job_application_tracking(
            approved_application
        )
    )

    applied_application = (
        orchestrator.update_job_application_status(
            tracked_application,
            JobStatus.APPLIED,
            "Candidatura enviada.",
        )
    )

    applied_events = [
        event
        for event in applied_application.tracking.history
        if event.status == JobStatus.APPLIED
    ]

    assert applied_events

    applied_at = applied_events[-1].occurred_at

    first_follow_up_at = applied_at + timedelta(
        days=5
    )

    first_follow_up = (
        orchestrator.register_job_application_follow_up(
            applied_application,
            occurred_at=first_follow_up_at,
        )
    )

    assert first_follow_up.tracking.followup_count == 1
    assert (
        first_follow_up.tracking.last_followup_at
        == first_follow_up_at
    )

    too_early_for_second = (
        first_follow_up_at + timedelta(days=6)
    )

    assert (
        orchestrator.should_follow_up_job_application(
            first_follow_up,
            now=too_early_for_second,
        )
        is False
    )

    second_follow_up_at = (
        first_follow_up_at + timedelta(days=7)
    )

    second_follow_up = (
        orchestrator.register_job_application_follow_up(
            first_follow_up,
            occurred_at=second_follow_up_at,
        )
    )

    assert second_follow_up.tracking.followup_count == 2
    assert (
        second_follow_up.tracking.last_followup_at
        == second_follow_up_at
    )

    assert (
        orchestrator.should_follow_up_job_application(
            second_follow_up,
            now=second_follow_up_at + timedelta(days=7),
        )
        is False
    )

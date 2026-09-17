from core.orchestrator.orchestrator import JobOrchestrator
from core.schemas.application import ApplicationDecision
from core.schemas.job import JobOpportunity, WorkModel


def test_orchestrator_prepares_application_for_human_approval():
    orchestrator = JobOrchestrator()

    job = JobOpportunity(
        job_id="application-flow-001",
        title="Analista de Dados Júnior",
        company="Empresa Teste",
        source="TEST",
        location="São Paulo",
        work_model=WorkModel.HYBRID,
        employment_type="CLT",
        description="Vaga para análise de dados.",
        requirements=[
            "Power BI",
            "SQL",
            "Excel",
            "Python",
            "DAX",
        ],
    )

    qualification = orchestrator.run([job])[0]

    preparation = orchestrator.prepare_application(
        job,
        qualification,
    )

    assert preparation.approved_for_human_review is True
    assert preparation.decision == (
        ApplicationDecision.PENDING_HUMAN_APPROVAL
    )
    assert preparation.ready_to_apply is False
    assert preparation.blocking_issues == []


def test_human_approval_makes_application_ready():
    orchestrator = JobOrchestrator()

    job = JobOpportunity(
        job_id="human-approval-001",
        title="Analista de Dados Júnior",
        company="Empresa Teste",
        source="TEST",
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

    qualification = orchestrator.run([job])[0]

    preparation = orchestrator.prepare_application(
        job,
        qualification,
    )

    assert preparation.ready_to_apply is False

    approved = orchestrator.approve_application(preparation)

    assert approved.decision == ApplicationDecision.APPROVED_BY_HUMAN
    assert approved.ready_to_apply is True


def test_orchestrator_starts_tracking_after_human_approval():
    from core.schemas.job import JobOpportunity, WorkModel

    orchestrator = JobOrchestrator()

    job = JobOpportunity(
        job_id="job-tracking-001",
        title="Analista de Dados Júnior",
        company="Empresa Teste",
        source="TESTE",
        location="São Paulo",
        work_model=WorkModel.HYBRID,
        requirements=[
            "Power BI",
            "SQL",
            "Python",
            "Excel",
        ],
    )

    qualification = orchestrator.run([job])[0]

    preparation = orchestrator.prepare_application(
        job,
        qualification,
    )

    approved = orchestrator.approve_application(preparation)

    tracking = orchestrator.start_tracking(approved)

    assert tracking.job_id == "job-tracking-001"
    assert tracking.current_status.value == "READY_TO_APPLY"
    assert len(tracking.history) == 1

def test_orchestrator_updates_tracking_to_applied():
    from core.schemas.job import JobOpportunity, JobStatus, WorkModel

    orchestrator = JobOrchestrator()

    job = JobOpportunity(
        job_id="job-tracking-002",
        title="Analista de Dados Júnior",
        company="Empresa Teste",
        source="TESTE",
        location="São Paulo",
        work_model=WorkModel.HYBRID,
        requirements=[
            "Power BI",
            "SQL",
            "Python",
            "Excel",
        ],
    )

    qualification = orchestrator.run([job])[0]

    preparation = orchestrator.prepare_application(
        job,
        qualification,
    )

    approved = orchestrator.approve_application(preparation)
    tracking = orchestrator.start_tracking(approved)

    updated = orchestrator.update_tracking_status(
        tracking,
        JobStatus.APPLIED,
        note="Candidatura enviada.",
    )

    assert updated.current_status == JobStatus.APPLIED
    assert len(updated.history) == 2
    assert updated.history[-1].status == JobStatus.APPLIED
    assert updated.history[-1].note == "Candidatura enviada."


def test_orchestrator_checks_followup_eligibility():
    from datetime import datetime, timedelta, timezone

    from core.schemas.job import JobStatus
    from core.schemas.tracking import ApplicationTracking

    orchestrator = JobOrchestrator()

    now = datetime.now(timezone.utc)
    last_contact = now - timedelta(days=5)

    tracking = ApplicationTracking(
        job_id="followup-integration-001",
        current_status=JobStatus.APPLIED,
    )

    result = orchestrator.should_follow_up(
        tracking=tracking,
        followup_count=0,
        last_contact_at=last_contact,
        now=now,
    )

    assert result is True


def test_orchestrator_calculates_optimization_metrics():
    from core.schemas.job import JobStatus
    from core.schemas.tracking import ApplicationTracking, TrackingEvent

    orchestrator = JobOrchestrator()

    tracking = ApplicationTracking(
        job_id="optimization-integration-001",
        current_status=JobStatus.REJECTED,
        history=[
            TrackingEvent(
                status=JobStatus.APPLIED,
                note="Candidatura enviada.",
            ),
            TrackingEvent(
                status=JobStatus.SCREENING,
                note="Triagem iniciada.",
            ),
            TrackingEvent(
                status=JobStatus.INTERVIEW,
                note="Entrevista realizada.",
            ),
            TrackingEvent(
                status=JobStatus.REJECTED,
                note="Processo encerrado.",
            ),
        ],
    )

    metrics = orchestrator.calculate_optimization_metrics(
        [tracking]
    )

    assert metrics["total_applications"] == 1
    assert metrics["screening_or_beyond"] == 1
    assert metrics["interviews"] == 1
    assert metrics["offers"] == 0
    assert metrics["hires"] == 0
    assert metrics["rejections"] == 1
    assert metrics["interview_rate"] == 100.0


def test_central_job_application_flow_until_applied():
    from core.schemas.job import JobOpportunity, JobStatus, WorkModel

    orchestrator = JobOrchestrator()

    job = JobOpportunity(
        job_id="central-flow-001",
        title="Analista de Dados Júnior",
        company="Empresa Teste",
        source="TESTE",
        location="São Paulo",
        work_model=WorkModel.HYBRID,
        requirements=[
            "Power BI",
            "SQL",
            "Python",
            "Excel",
        ],
    )

    application = orchestrator.create_job_application(
        job=job,
        application_id="application-central-001",
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
        note="Candidatura enviada.",
    )

    assert application.qualification is not None
    assert application.personalization is not None
    assert application.preparation is not None
    assert application.preparation.ready_to_apply is True
    assert application.tracking is not None
    assert application.tracking.current_status == JobStatus.APPLIED
    assert application.tracking.history[-1].status == JobStatus.APPLIED
    assert application.tracking.history[-1].note == "Candidatura enviada."


def test_orchestrator_saves_gets_and_lists_job_application():
    from core.schemas.job import JobOpportunity

    orchestrator = JobOrchestrator()

    job = JobOpportunity(
        job_id="repository-integration-job-001",
        title="Analista de Dados Júnior",
        company="Empresa Teste",
        source="TESTE",
    )

    application = orchestrator.create_job_application(
        job=job,
        application_id="repository-integration-001",
    )

    orchestrator.save_job_application(application)

    saved = orchestrator.get_job_application(
        "repository-integration-001"
    )

    applications = orchestrator.list_job_applications()

    assert saved is not None
    assert saved.application_id == "repository-integration-001"
    assert saved.job.job_id == "repository-integration-job-001"
    assert len(applications) == 1
    assert applications[0].application_id == "repository-integration-001"





from core.orchestrator.orchestrator import JobOrchestrator
from core.schemas.job import JobOpportunity, JobStatus, WorkModel


def test_orchestrator_runs_full_pipeline_and_sorts_by_fit():
    jobs = [
        JobOpportunity(
            job_id="vaga-001",
            title="Analista de Dados Júnior",
            company="Empresa A",
            source="TESTE",
            location="São Paulo",
            work_model=WorkModel.HYBRID,
            employment_type="CLT",
            requirements=["Power BI", "SQL", "Excel", "Python", "DAX"],
        ),
        JobOpportunity(
            job_id="vaga-002",
            title="Analista de BI Júnior",
            company="Empresa B",
            source="TESTE",
            location="São Paulo",
            work_model=WorkModel.REMOTE,
            employment_type="CLT",
            requirements=["Power BI", "SQL", "DAX", "ETL"],
        ),
        JobOpportunity(
            job_id="vaga-003",
            title="Engenheiro DevOps Sênior",
            company="Empresa C",
            source="TESTE",
            location="Outra Localidade",
            work_model=WorkModel.ONSITE,
            employment_type="CLT",
            requirements=["Kubernetes", "Terraform", "AWS", "Jenkins"],
        ),
    ]

    results = JobOrchestrator().run(jobs)

    assert len(results) == 3

    assert results[0].fit_score >= results[1].fit_score
    assert results[1].fit_score >= results[2].fit_score

    assert results[0].recommendation == "RECOMENDADA"
    assert results[2].recommendation == "NAO_RECOMENDADA"

    assert results[2].job_id == "vaga-003"


def test_orchestrator_blocks_tracking_before_human_approval():
    orchestrator = JobOrchestrator()

    job = JobOpportunity(
        job_id="tracking-approval-001",
        title="Analista de Dados Júnior",
        company="Empresa Teste",
        source="TESTE",
        location="São Paulo",
        work_model=WorkModel.REMOTE,
        employment_type="CLT",
        requirements=["Power BI", "SQL", "Excel"],
    )

    application = orchestrator.create_job_application(
        job=job,
        application_id="application-tracking-approval-001",
    )

    application = orchestrator.qualify_job_application(application)
    application = orchestrator.personalize_job_application(application)
    application = orchestrator.prepare_job_application(application)

    try:
        orchestrator.start_job_application_tracking(application)

        assert False, (
            "O tracking não deveria iniciar antes da aprovação humana."
        )

    except ValueError as error:
        assert str(error) == (
            "A candidatura precisa estar aprovada antes do acompanhamento."
        )


def test_orchestrator_runs_application_tracking_flow():
    orchestrator = JobOrchestrator()

    job = JobOpportunity(
        job_id="tracking-flow-001",
        title="Analista de Dados Júnior",
        company="Empresa Teste",
        source="TESTE",
        location="São Paulo",
        work_model=WorkModel.REMOTE,
        employment_type="CLT",
        requirements=["Power BI", "SQL", "Excel"],
    )

    application = orchestrator.create_job_application(
        job=job,
        application_id="application-tracking-flow-001",
    )

    application = orchestrator.qualify_job_application(application)
    application = orchestrator.personalize_job_application(application)
    application = orchestrator.prepare_job_application(application)

    assert application.preparation is not None

    application = orchestrator.approve_job_application(application)

    assert application.preparation is not None
    assert application.preparation.ready_to_apply is True

    application = orchestrator.start_job_application_tracking(
        application
    )

    assert application.tracking is not None
    assert application.tracking.job_id == "tracking-flow-001"
    assert application.tracking.current_status == JobStatus.READY_TO_APPLY
    assert len(application.tracking.history) == 1

    application = orchestrator.update_job_application_status(
        application,
        JobStatus.APPLIED,
        note="Candidatura enviada.",
    )

    assert application.tracking is not None
    assert application.tracking.current_status == JobStatus.APPLIED
    assert len(application.tracking.history) == 2

    assert application.tracking.history[0].status == (
        JobStatus.READY_TO_APPLY
    )
    assert application.tracking.history[1].status == JobStatus.APPLIED
    assert application.tracking.history[1].note == (
        "Candidatura enviada."
    )

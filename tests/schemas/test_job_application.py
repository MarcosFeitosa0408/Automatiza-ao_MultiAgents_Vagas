from core.schemas.job import JobOpportunity, WorkModel
from core.schemas.job_application import JobApplicationObject


def test_job_application_object_accepts_discovered_job():
    job = JobOpportunity(
        job_id="job-application-001",
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

    application = JobApplicationObject(
        application_id="application-001",
        job=job,
    )

    assert application.application_id == "application-001"
    assert application.job.job_id == "job-application-001"
    assert application.qualification is None
    assert application.personalization is None
    assert application.preparation is None
    assert application.tracking is None


def test_job_application_object_has_timestamps():
    job = JobOpportunity(
        job_id="job-application-002",
        title="Analista de BI Júnior",
        company="Empresa Teste",
        source="TESTE",
    )

    application = JobApplicationObject(
        application_id="application-002",
        job=job,
    )

    assert application.created_at is not None
    assert application.updated_at is not None

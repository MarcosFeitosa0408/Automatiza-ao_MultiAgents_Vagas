from core.orchestrator.orchestrator import JobOrchestrator
from core.schemas.job import JobOpportunity, WorkModel


def test_orchestrator_qualification_to_personalization_flow():
    orchestrator = JobOrchestrator()

    job = JobOpportunity(
        job_id="integration-personalization-001",
        title="Analista de Dados Júnior",
        company="Empresa Integração",
        source="TEST",
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

    qualification = orchestrator.run([job])[0]

    personalization = orchestrator.personalize_job(
        job,
        qualification,
    )

    assert personalization.job_id == job.job_id
    assert personalization.evidence_verified is True
    assert "Power BI" in personalization.selected_skills
    assert "SQL" in personalization.selected_skills
    assert personalization.professional_title
    assert personalization.professional_summary

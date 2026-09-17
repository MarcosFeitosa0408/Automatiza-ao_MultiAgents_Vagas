from core.orchestrator.orchestrator import JobOrchestrator
from core.schemas.job import JobOpportunity, WorkModel


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

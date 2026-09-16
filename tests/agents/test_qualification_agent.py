from agents.agent_00_memory.memory_agent import MemoryAgent
from agents.agent_02_qualification.qualification_agent import QualificationAgent
from core.schemas.job import JobOpportunity, WorkModel


def test_qualification_agent_calculates_candidate_fit():
    profile = MemoryAgent().load_profile()

    job = JobOpportunity(
        job_id="vaga-fit-001",
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
            "Azure",
        ],
    )

    result = QualificationAgent().calculate_fit(job, profile)

    assert result.job_id == "vaga-fit-001"
    assert 0 <= result.fit_score <= 10
    assert result.recommendation == "RECOMENDADA"

    assert "power bi" in result.matched_skills
    assert "sql" in result.matched_skills
    assert "python" in result.matched_skills
    assert "azure" in result.missing_skills

    assert result.breakdown.seniority == 10.0
    assert result.breakdown.location_work_model == 10.0


def test_qualification_agent_rejects_low_fit_job():
    profile = MemoryAgent().load_profile()

    job = JobOpportunity(
        job_id="vaga-fit-002",
        title="Engenheiro DevOps Sênior",
        company="Empresa Teste",
        source="TESTE",
        location="Outra Localidade",
        work_model=WorkModel.ONSITE,
        employment_type="CLT",
        requirements=[
            "Kubernetes",
            "Terraform",
            "AWS",
            "Jenkins",
        ],
    )

    result = QualificationAgent().calculate_fit(job, profile)

    assert result.fit_score < 6.5
    assert result.recommendation == "NAO_RECOMENDADA"
    assert len(result.matched_skills) == 0
    assert len(result.missing_skills) == 4

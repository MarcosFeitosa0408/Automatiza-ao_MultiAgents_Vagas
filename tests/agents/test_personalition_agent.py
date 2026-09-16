from agents.agent_00_memory.memory_agent import MemoryAgent
from agents.agent_02_qualification.qualification_agent import QualificationAgent
from agents.agent_03_personalization.personalization_agent import PersonalizationAgent
from core.schemas.job import JobOpportunity, WorkModel


def test_personalization_agent_uses_only_verified_profile_data():
    profile = MemoryAgent().load_profile()

    job = JobOpportunity(
        job_id="personalization-001",
        title="Analista de Dados Júnior",
        company="Empresa Teste",
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
            "Apache Spark",
        ],
    )

    qualification = QualificationAgent().calculate_fit(
        job,
        profile,
    )

    result = PersonalizationAgent().personalize(
        job,
        profile,
        qualification,
    )

    assert result.job_id == "personalization-001"
    assert result.evidence_verified is True

    assert "Power BI" in result.selected_skills
    assert "SQL" in result.selected_skills
    assert "Python" in result.selected_skills

    assert "Apache Spark" not in result.selected_skills
    assert "apache spark" in result.unsupported_requirements

    assert "Power BI" in result.ats_keywords
    assert "SQL" in result.ats_keywords

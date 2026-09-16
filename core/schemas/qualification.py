from pydantic import Field

from core.schemas.job import StrictModel


class QualificationBreakdown(StrictModel):
    """Pontuação detalhada dos critérios de qualificação."""

    technical_skills: float = Field(ge=0, le=10)
    professional_experience: float = Field(ge=0, le=10)
    responsibilities: float = Field(ge=0, le=10)
    seniority: float = Field(ge=0, le=10)
    location_work_model: float = Field(ge=0, le=10)
    ats_compatibility: float = Field(ge=0, le=10)


class QualificationResult(StrictModel):
    """Resultado final da análise de compatibilidade candidato-vaga."""

    job_id: str = Field(min_length=1)
    fit_score: float = Field(ge=0, le=10)

    recommendation: str

    matched_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)

    eliminatory_gaps: list[str] = Field(default_factory=list)

    breakdown: QualificationBreakdown

    reasoning: list[str] = Field(default_factory=list)

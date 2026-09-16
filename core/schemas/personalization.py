from pydantic import Field

from core.schemas.job import StrictModel


class PersonalizationResult(StrictModel):
    """Conteúdo profissional selecionado e adaptado para uma vaga."""

    job_id: str = Field(min_length=1)

    professional_title: str = Field(min_length=1)
    professional_summary: str = Field(min_length=1)

    selected_skills: list[str] = Field(default_factory=list)
    selected_experiences: list[str] = Field(default_factory=list)
    selected_projects: list[str] = Field(default_factory=list)

    ats_keywords: list[str] = Field(default_factory=list)

    unsupported_requirements: list[str] = Field(default_factory=list)

    evidence_verified: bool = True

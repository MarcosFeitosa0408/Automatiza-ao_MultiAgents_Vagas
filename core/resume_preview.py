from pydantic import Field

from core.schemas.candidate import (
    Education,
    Experience,
    MasterProfile,
    Project,
)
from core.schemas.job import StrictModel
from core.schemas.personalization import PersonalizationResult


class ResumePreview(StrictModel):
    application_id: str
    job_title: str
    company: str

    name: str
    email: str
    phone: str
    location: str

    professional_title: str
    professional_summary: str
    skills: list[str]

    education: list[Education]
    experience: list[Experience]
    projects: list[Project]

    languages: dict[str, str]
    links: dict[str, str]

    ats_keywords: list[str]
    unsupported_requirements: list[str]
    warnings: list[str] = Field(default_factory=list)


def build_resume_preview(
    application_id: str,
    job_title: str,
    company: str,
    profile: MasterProfile,
    personalization: PersonalizationResult,
) -> ResumePreview:
    """Organiza somente informações existentes no perfil mestre."""

    selected_experiences = set(personalization.selected_experiences)
    selected_projects = set(personalization.selected_projects)

    experiences = [
        experience
        for experience in profile.experience
        if f"{experience.role} - {experience.company}"
        in selected_experiences
    ]

    projects = [
        project
        for project in profile.projects
        if project.name in selected_projects
        and project.authorized_for_portfolio is not False
    ]

    warnings: list[str] = []

    def missing(value: str | None) -> bool:
        return not value or value.strip().casefold() in (
            "", "nao_identificado", "não identificado", "n/a", "na",
        )

    if missing(profile.candidate.name):
        warnings.append("Preencha seu nome em Meu perfil > Identificação e apresentação.")

    if missing(personalization.professional_title):
        warnings.append("Confira o título profissional em Meu perfil > Identificação e apresentação.")
    if missing(personalization.professional_summary):
        warnings.append("Preencha o resumo em Meu perfil > Identificação e apresentação e gere outra prévia.")

    if missing(profile.candidate.email):
        warnings.append("Preencha o e-mail de contato no perfil.")

    if missing(profile.candidate.phone):
        warnings.append("Preencha o telefone de contato no perfil.")

    if not personalization.selected_skills:
        warnings.append(
            "Nenhuma competência foi selecionada para os requisitos informados."
        )

    if any(
        not experience.current and missing(getattr(experience, "end", None))
        for experience in experiences
    ):
        warnings.append(
            "Confira a data de término das experiências encerradas."
        )

    if missing(profile.candidate.location.city) or missing(profile.candidate.location.country):
        warnings.append("Confira cidade e país em Meu perfil > Identificação e apresentação. Endereço completo não é necessário.")

    if not profile.education:
        warnings.append("Nenhuma formação cadastrada. Inclua em Meu perfil > Formação apenas se fizer parte da sua trajetória.")
    elif any(missing(item.degree) or missing(item.institution) or missing(item.status) for item in profile.education):
        warnings.append("Complete curso, instituição e situação das formações em Meu perfil > Formação.")

    if any(missing(item.role) or missing(item.company) or missing(item.start) for item in experiences):
        warnings.append("Confira cargo, empresa e data de início das experiências selecionadas em Meu perfil > Experiências.")
    if any(not item.responsibilities and not item.achievements for item in experiences):
        warnings.append("Descreva atividades ou resultados reais das experiências em Meu perfil > Experiências.")
    if any(missing(item.name) or missing(item.description) for item in projects):
        warnings.append("Complete nome e descrição dos projetos selecionados em Meu perfil > Projetos.")
    if not experiences and not projects:
        warnings.append("Nenhuma experiência ou projeto foi selecionado para esta vaga. Confira seus dados e os requisitos; não inclua experiências que não possui.")

    warnings.append(
        "Revise o conteúdo antes de usar. Esta prévia não envia candidatura "
        "e não garante aprovação em uma seleção."
    )

    location = ", ".join(
        value.strip()
        for value in (
            profile.candidate.location.city,
            profile.candidate.location.state,
            profile.candidate.location.country,
        )
        if value.strip()
    )

    return ResumePreview(
        application_id=application_id,
        job_title=job_title,
        company=company,
        name=profile.candidate.name,
        email=profile.candidate.email,
        phone=profile.candidate.phone,
        location=location,
        professional_title=personalization.professional_title,
        professional_summary=personalization.professional_summary,
        skills=personalization.selected_skills,
        education=profile.education,
        experience=experiences,
        projects=projects,
        languages=profile.languages.model_dump(),
        links=profile.portfolio.model_dump(),
        ats_keywords=personalization.ats_keywords,
        unsupported_requirements=personalization.unsupported_requirements,
        warnings=warnings,
    )

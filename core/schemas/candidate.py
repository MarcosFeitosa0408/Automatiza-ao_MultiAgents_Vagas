from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    """Modelo-base que rejeita campos inesperados."""

    model_config = ConfigDict(extra="forbid")


class Location(StrictModel):
    city: str
    state: str
    country: str


class EmploymentStatus(StrictModel):
    currently_clt: bool
    actively_seeking: bool
    priority: str
    primary_goal: str


class CareerTarget(StrictModel):
    primary_roles: list[str]
    secondary_roles: list[str]
    seniority: list[str]


class WorkPreferences(StrictModel):
    employment_type_priority: list[str]
    remote: bool
    hybrid: bool
    onsite: bool
    preferred_location: list[str]
    relocation: bool


class CandidateData(StrictModel):
    name: str
    location: Location
    employment_status: EmploymentStatus
    career_target: CareerTarget
    work_preferences: WorkPreferences


class ProfessionalPositioning(StrictModel):
    title: str
    summary: str
    focus: list[str]


class Education(StrictModel):
    degree: str
    institution: str
    status: str


class Skills(StrictModel):
    core: list[str]
    database: list[str]
    python: list[str]
    analytics: list[str]
    tools: list[str]
    automation: list[str]


class Achievement(StrictModel):
    metric: str
    value: int | float
    description: str
    unit: str | None = None
    approximate: bool = False
    period: str | None = None


class Experience(StrictModel):
    company: str
    role: str
    employment_type: str
    start: str
    current: bool
    location: str
    work_model: str
    technologies: list[str]
    responsibilities: list[str]
    achievements: list[Achievement]


class Project(StrictModel):
    name: str
    description: str
    technologies: list[str]
    context: str | None = None
    authorized_for_portfolio: bool | None = None


class Languages(StrictModel):
    portuguese: str
    english: str


class Portfolio(StrictModel):
    portfolio_url: str
    github_url: str
    linkedin_url: str


class EvidencePolicy(StrictModel):
    master_profile_is_source_of_truth: bool
    never_invent_skill: bool
    never_invent_experience: bool
    never_invent_education: bool
    never_invent_certification: bool
    never_invent_result: bool
    never_invent_salary: bool
    never_invent_job: bool
    unknown_value: str


class MasterProfile(StrictModel):
    """Representação validada da fonte oficial de dados do candidato."""

    schema_version: str = Field(min_length=1)
    candidate_id: str = Field(min_length=1)

    candidate: CandidateData
    professional_positioning: ProfessionalPositioning
    education: list[Education]
    skills: Skills
    experience: list[Experience]
    projects: list[Project]
    languages: Languages
    portfolio: Portfolio
    evidence_policy: EvidencePolicy

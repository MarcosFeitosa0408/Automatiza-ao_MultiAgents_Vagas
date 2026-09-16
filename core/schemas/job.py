from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class StrictModel(BaseModel):
    """Modelo-base que rejeita campos inesperados."""

    model_config = ConfigDict(extra="forbid")


class WorkModel(str, Enum):
    REMOTE = "REMOTE"
    HYBRID = "HYBRID"
    ONSITE = "ONSITE"
    UNKNOWN = "UNKNOWN"


class JobStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    QUALIFIED = "QUALIFIED"
    VALIDATION_REVIEW = "VALIDATION_REVIEW"
    APPROVED = "APPROVED"
    READY_TO_APPLY = "READY_TO_APPLY"
    APPLIED = "APPLIED"
    SCREENING = "SCREENING"
    INTERVIEW = "INTERVIEW"
    FINAL = "FINAL"
    OFFER = "OFFER"
    HIRED = "HIRED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"
    NO_RESPONSE = "NO_RESPONSE"
    EXPIRED = "EXPIRED"
    APPLICATION_FAILED = "APPLICATION_FAILED"


class JobOpportunity(StrictModel):
    """Representação padronizada de uma vaga descoberta."""

    job_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    company: str = Field(min_length=1)

    source: str = Field(min_length=1)
    url: HttpUrl | None = None

    location: str = "NAO_IDENTIFICADO"
    work_model: WorkModel = WorkModel.UNKNOWN
    employment_type: str = "NAO_IDENTIFICADO"

    description: str = ""
    requirements: list[str] = Field(default_factory=list)
    desirable_requirements: list[str] = Field(default_factory=list)

    discovered_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    status: JobStatus = JobStatus.DISCOVERED

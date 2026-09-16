from pydantic import Field

from core.schemas.job import JobOpportunity, StrictModel, WorkModel


class JobAnalysisRequest(StrictModel):
    """Dados recebidos pela API para análise de uma vaga."""

    job_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    company: str = Field(min_length=1)

    source: str = "API"
    location: str = "NAO_IDENTIFICADO"
    work_model: WorkModel = WorkModel.UNKNOWN
    employment_type: str = "NAO_IDENTIFICADO"

    description: str = ""
    requirements: list[str] = Field(default_factory=list)
    desirable_requirements: list[str] = Field(default_factory=list)


from core.schemas.application import ApplicationPreparation
from core.schemas.job import JobStatus
from core.schemas.tracking import ApplicationTracking


class ApplicationDecisionRequest(StrictModel):
    """Recebe uma candidatura preparada para decisão humana."""

    application: ApplicationPreparation


class TrackingStatusUpdateRequest(StrictModel):
    """Recebe a atualização de status de uma candidatura."""

    tracking: ApplicationTracking
    new_status: JobStatus
    note: str = ""


class StoredTrackingStatusUpdateRequest(StrictModel):
    """Recebe a atualização de status de uma candidatura armazenada."""

    new_status: JobStatus
    note: str = ""


class JobApplicationCreateRequest(StrictModel):
    application_id: str = Field(min_length=1)
    job: JobOpportunity



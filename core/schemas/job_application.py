from datetime import datetime, timezone

from pydantic import Field

from core.schemas.application import ApplicationPreparation
from core.schemas.job import JobOpportunity, StrictModel
from core.schemas.personalization import PersonalizationResult
from core.schemas.qualification import QualificationResult
from core.schemas.tracking import ApplicationTracking


class JobApplicationObject(StrictModel):
    """Objeto central que representa uma candidatura no pipeline."""

    application_id: str = Field(min_length=1)

    job: JobOpportunity
    qualification: QualificationResult | None = None
    personalization: PersonalizationResult | None = None
    preparation: ApplicationPreparation | None = None
    tracking: ApplicationTracking | None = None

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

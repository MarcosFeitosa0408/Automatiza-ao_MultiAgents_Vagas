from datetime import datetime, timezone

from pydantic import Field

from core.schemas.job import JobStatus, StrictModel


class TrackingEvent(StrictModel):
    """Evento registrado no histórico de uma candidatura."""

    status: JobStatus
    note: str = ""
    occurred_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class ApplicationTracking(StrictModel):
    """Estado atual e histórico de uma candidatura."""

    job_id: str = Field(min_length=1)
    current_status: JobStatus
    history: list[TrackingEvent] = Field(default_factory=list)
    followup_count: int = Field(default=0, ge=0)
    last_followup_at: datetime | None = None

from enum import Enum

from pydantic import Field

from core.schemas.job import StrictModel


class ApplicationDecision(str, Enum):
    PENDING_HUMAN_APPROVAL = "PENDING_HUMAN_APPROVAL"
    APPROVED_BY_HUMAN = "APPROVED_BY_HUMAN"
    REJECTED_BY_HUMAN = "REJECTED_BY_HUMAN"


class ApplicationPreparation(StrictModel):
    """Estado da candidatura antes do envio efetivo."""

    job_id: str = Field(min_length=1)
    approved_for_human_review: bool

    decision: ApplicationDecision = (
        ApplicationDecision.PENDING_HUMAN_APPROVAL
    )

    ready_to_apply: bool = False

    blocking_issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

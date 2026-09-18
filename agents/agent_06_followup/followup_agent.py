from datetime import datetime, timedelta, timezone

from core.schemas.job import JobStatus
from core.schemas.tracking import ApplicationTracking


class FollowUpAgent:
    """Controla o momento adequado para follow-up de candidaturas."""

    MAX_FOLLOWUPS = 2
    FIRST_FOLLOWUP_DAYS = 5
    SECOND_FOLLOWUP_DAYS = 7

    TERMINAL_STATUSES = {
        JobStatus.REJECTED,
        JobStatus.WITHDRAWN,
        JobStatus.EXPIRED,
        JobStatus.APPLICATION_FAILED,
        JobStatus.OFFER,
        JobStatus.HIRED,
    }

    def should_follow_up(
        self,
        tracking: ApplicationTracking,
        followup_count: int,
        last_contact_at: datetime,
        now: datetime | None = None,
    ) -> bool:
        """Retorna True quando a candidatura está apta para follow-up."""

        if tracking.current_status in self.TERMINAL_STATUSES:
            return False

        if tracking.current_status not in {
            JobStatus.APPLIED,
            JobStatus.SCREENING,
        }:
            return False

        if followup_count >= self.MAX_FOLLOWUPS:
            return False

        current_time = now or datetime.now(timezone.utc)

        waiting_days = (
            self.FIRST_FOLLOWUP_DAYS
            if followup_count == 0
            else self.SECOND_FOLLOWUP_DAYS
        )

        next_followup_at = last_contact_at + timedelta(
            days=waiting_days
        )

        return current_time >= next_followup_at

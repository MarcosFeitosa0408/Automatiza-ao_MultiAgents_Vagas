from core.schemas.job import JobStatus
from core.schemas.tracking import ApplicationTracking, TrackingEvent


class TrackingAgent:
    """Registra e acompanha a evolução de uma candidatura."""

    ALLOWED_TRANSITIONS = {
        JobStatus.READY_TO_APPLY: {
            JobStatus.APPLIED,
            JobStatus.WITHDRAWN,
            JobStatus.APPLICATION_FAILED,
        },
        JobStatus.APPLIED: {
            JobStatus.SCREENING,
            JobStatus.INTERVIEW,
            JobStatus.REJECTED,
            JobStatus.NO_RESPONSE,
            JobStatus.WITHDRAWN,
        },
        JobStatus.SCREENING: {
            JobStatus.INTERVIEW,
            JobStatus.REJECTED,
            JobStatus.NO_RESPONSE,
            JobStatus.WITHDRAWN,
        },
        JobStatus.INTERVIEW: {
            JobStatus.FINAL,
            JobStatus.OFFER,
            JobStatus.REJECTED,
            JobStatus.WITHDRAWN,
        },
        JobStatus.FINAL: {
            JobStatus.OFFER,
            JobStatus.REJECTED,
            JobStatus.WITHDRAWN,
        },
        JobStatus.OFFER: {
            JobStatus.HIRED,
            JobStatus.REJECTED,
            JobStatus.WITHDRAWN,
        },
    }

    def start_tracking(
        self,
        job_id: str,
        initial_status: JobStatus = JobStatus.READY_TO_APPLY,
    ) -> ApplicationTracking:
        event = TrackingEvent(
            status=initial_status,
            note="Acompanhamento da candidatura iniciado.",
        )

        return ApplicationTracking(
            job_id=job_id,
            current_status=initial_status,
            history=[event],
        )

    def update_status(
        self,
        tracking: ApplicationTracking,
        new_status: JobStatus,
        note: str = "",
    ) -> ApplicationTracking:
        allowed_statuses = self.ALLOWED_TRANSITIONS.get(
            tracking.current_status,
            set(),
        )

        if new_status not in allowed_statuses:
            raise ValueError(
                f"Transição inválida: "
                f"{tracking.current_status.value} -> {new_status.value}"
            )
            
        event = TrackingEvent(
            status=new_status,
            note=note,
        )

        return tracking.model_copy(
            update={
                "current_status": new_status,
                "history": tracking.history + [event],
            }
        )

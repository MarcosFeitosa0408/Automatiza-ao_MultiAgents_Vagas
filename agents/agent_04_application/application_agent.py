from core.schemas.application import (
    ApplicationDecision,
    ApplicationPreparation,
)


class ApplicationAgent:
    """Controla a preparação da candidatura com aprovação humana obrigatória."""

    def prepare(
        self,
        job_id: str,
        approved_for_human_review: bool,
        blocking_issues: list[str],
        warnings: list[str],
    ) -> ApplicationPreparation:
        decision = ApplicationDecision.PENDING_HUMAN_APPROVAL

        return ApplicationPreparation(
            job_id=job_id,
            approved_for_human_review=approved_for_human_review,
            decision=decision,
            ready_to_apply=False,
            blocking_issues=blocking_issues,
            warnings=warnings,
        )

    def approve(
        self,
        preparation: ApplicationPreparation,
    ) -> ApplicationPreparation:
        if not preparation.approved_for_human_review:
            return preparation.model_copy(
                update={
                    "ready_to_apply": False,
                }
            )

        return preparation.model_copy(
            update={
                "decision": ApplicationDecision.APPROVED_BY_HUMAN,
                "ready_to_apply": True,
            }
        )

    def reject(
        self,
        preparation: ApplicationPreparation,
    ) -> ApplicationPreparation:
        return preparation.model_copy(
            update={
                "decision": ApplicationDecision.REJECTED_BY_HUMAN,
                "ready_to_apply": False,
            }
        )

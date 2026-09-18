from core.schemas.job import JobStatus
from core.schemas.tracking import ApplicationTracking


class OptimizationAgent:
    """Analisa resultados reais do funil de candidaturas."""

    def calculate_metrics(
        self,
        applications: list[ApplicationTracking],
    ) -> dict:
        """Calcula métricas usando apenas candidaturas registradas."""

        total = len(applications)

        if total == 0:
            return {
                "total_applications": 0,
                "screening_or_beyond": 0,
                "interviews": 0,
                "finals": 0,
                "offers": 0,
                "hires": 0,
                "rejections": 0,
                "response_rate": 0.0,
                "interview_rate": 0.0,
                "offer_rate": 0.0,
                "hire_rate": 0.0,
            }

        screening_or_beyond = self._count_reached_status(
            applications,
            {
                JobStatus.SCREENING,
                JobStatus.INTERVIEW,
                JobStatus.FINAL,
                JobStatus.OFFER,
                JobStatus.HIRED,
            },
        )

        interviews = self._count_reached_status(
            applications,
            {
                JobStatus.INTERVIEW,
                JobStatus.FINAL,
                JobStatus.OFFER,
                JobStatus.HIRED,
            },
        )

        finals = self._count_reached_status(
            applications,
            {
                JobStatus.FINAL,
                JobStatus.OFFER,
                JobStatus.HIRED,
            },
        )

        offers = self._count_reached_status(
            applications,
            {
                JobStatus.OFFER,
                JobStatus.HIRED,
            },
        )

        hires = self._count_reached_status(
            applications,
            {JobStatus.HIRED},
        )

        rejections = self._count_reached_status(
            applications,
            {JobStatus.REJECTED},
        )

        return {
            "total_applications": total,
            "screening_or_beyond": screening_or_beyond,
            "interviews": interviews,
            "finals": finals,
            "offers": offers,
            "hires": hires,
            "rejections": rejections,
            "response_rate": round(
                screening_or_beyond / total * 100,
                2,
            ),
            "interview_rate": round(
                interviews / total * 100,
                2,
            ),
            "offer_rate": round(
                offers / total * 100,
                2,
            ),
            "hire_rate": round(
                hires / total * 100,
                2,
            ),
        }

    def _count_reached_status(
        self,
        applications: list[ApplicationTracking],
        statuses: set[JobStatus],
    ) -> int:
        """Conta candidaturas que atingiram algum dos status informados."""

        count = 0

        for application in applications:
            reached_statuses = {
                event.status
                for event in application.history
            }

            reached_statuses.add(application.current_status)

            if reached_statuses & statuses:
                count += 1

        return count

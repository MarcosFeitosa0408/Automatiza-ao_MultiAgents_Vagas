from core.schemas.personalization import PersonalizationResult
from core.schemas.qualification import QualificationResult


class ValidationGate:
    """Valida se uma vaga pode seguir para aprovação humana."""

    def validate(
        self,
        qualification: QualificationResult,
        personalization: PersonalizationResult,
    ) -> dict:
        blocking_issues: list[str] = []
        warnings: list[str] = []

        if qualification.fit_score < 6.5:
            blocking_issues.append("FIT_ABAIXO_DO_LIMITE")

        if not personalization.evidence_verified:
            blocking_issues.append("EVIDENCIA_NAO_VERIFICADA")

        if qualification.eliminatory_gaps:
            blocking_issues.append("LACUNA_ELIMINATORIA")

        if personalization.unsupported_requirements:
            warnings.append("REQUISITOS_NAO_COMPROVADOS")

        approved_for_human_review = len(blocking_issues) == 0

        return {
            "approved_for_human_review": approved_for_human_review,
            "blocking_issues": blocking_issues,
            "warnings": warnings,
        }

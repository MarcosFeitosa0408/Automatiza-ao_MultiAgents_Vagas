from core.schemas.personalization import PersonalizationResult
from core.schemas.qualification import (
    QualificationBreakdown,
    QualificationResult,
)
from core.validation.validation_gate import ValidationGate


def build_qualification(
    fit_score: float,
    eliminatory_gaps: list[str] | None = None,
) -> QualificationResult:
    return QualificationResult(
        job_id="validation-001",
        fit_score=fit_score,
        recommendation="RECOMENDADA",
        matched_skills=["power bi", "sql"],
        missing_skills=[],
        eliminatory_gaps=eliminatory_gaps or [],
        breakdown=QualificationBreakdown(
            technical_skills=8,
            professional_experience=7,
            responsibilities=8,
            seniority=10,
            location_work_model=10,
            ats_compatibility=8,
        ),
        reasoning=[],
    )


def build_personalization(
    unsupported_requirements: list[str],
    evidence_verified: bool = True,
) -> PersonalizationResult:
    return PersonalizationResult(
        job_id="validation-001",
        professional_title="Analista de Dados Júnior",
        professional_summary="Resumo profissional validado.",
        selected_skills=["Power BI", "SQL"],
        selected_experiences=["Analista de Dados - Nerdcell"],
        selected_projects=[],
        ats_keywords=["Power BI", "SQL"],
        unsupported_requirements=unsupported_requirements,
        evidence_verified=evidence_verified,
    )


def test_validation_gate_approves_valid_application():
    gate = ValidationGate()

    result = gate.validate(
        build_qualification(8.0),
        build_personalization([]),
    )

    assert result["approved_for_human_review"] is True
    assert result["blocking_issues"] == []
    assert result["warnings"] == []


def test_validation_gate_warns_about_unsupported_requirement():
    gate = ValidationGate()

    result = gate.validate(
        build_qualification(8.0),
        build_personalization(["apache spark"]),
    )

    assert result["approved_for_human_review"] is True
    assert result["blocking_issues"] == []
    assert "REQUISITOS_NAO_COMPROVADOS" in result["warnings"]


def test_validation_gate_blocks_low_fit():
    gate = ValidationGate()

    result = gate.validate(
        build_qualification(6.0),
        build_personalization([]),
    )

    assert result["approved_for_human_review"] is False
    assert "FIT_ABAIXO_DO_LIMITE" in result["blocking_issues"]


def test_validation_gate_blocks_eliminatory_gap():
    gate = ValidationGate()

    result = gate.validate(
        build_qualification(
            8.0,
            eliminatory_gaps=["INGLES_FLUENTE_OBRIGATORIO"],
        ),
        build_personalization([]),
    )

    assert result["approved_for_human_review"] is False
    assert "LACUNA_ELIMINATORIA" in result["blocking_issues"]

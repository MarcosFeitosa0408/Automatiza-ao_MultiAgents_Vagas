from core.schemas.job import JobOpportunity
from core.schemas.candidate import MasterProfile
from core.schemas.qualification import (
    QualificationBreakdown,
    QualificationResult,
)


class QualificationAgent:
    """Calcula a compatibilidade entre candidato e vaga."""

    WEIGHTS = {
        "technical_skills": 0.35,
        "professional_experience": 0.20,
        "responsibilities": 0.15,
        "seniority": 0.10,
        "location_work_model": 0.10,
        "ats_compatibility": 0.10,
    }

    def calculate_fit(
        self,
        job: JobOpportunity,
        profile: MasterProfile,
    ) -> QualificationResult:
        candidate_skills = {
            skill.lower()
            for skill in (
                profile.skills.core
                + profile.skills.database
                + profile.skills.python
                + profile.skills.analytics
                + profile.skills.tools
                + profile.skills.automation
            )
        }

        job_requirements = {
            requirement.lower()
            for requirement in job.requirements
        }

        matched = sorted(candidate_skills & job_requirements)
        missing = sorted(job_requirements - candidate_skills)

        if job_requirements:
            technical_score = (
                len(matched) / len(job_requirements)
            ) * 10
        else:
            technical_score = 5.0

        experience_score = 7.0 if profile.experience else 0.0
        responsibilities_score = technical_score
        seniority_score = self._score_seniority(job, profile)
        location_score = self._score_location(job, profile)
        ats_score = technical_score

        breakdown = QualificationBreakdown(
            technical_skills=round(technical_score, 2),
            professional_experience=round(experience_score, 2),
            responsibilities=round(responsibilities_score, 2),
            seniority=round(seniority_score, 2),
            location_work_model=round(location_score, 2),
            ats_compatibility=round(ats_score, 2),
        )

        fit_score = round(
            breakdown.technical_skills
            * self.WEIGHTS["technical_skills"]
            + breakdown.professional_experience
            * self.WEIGHTS["professional_experience"]
            + breakdown.responsibilities
            * self.WEIGHTS["responsibilities"]
            + breakdown.seniority
            * self.WEIGHTS["seniority"]
            + breakdown.location_work_model
            * self.WEIGHTS["location_work_model"]
            + breakdown.ats_compatibility
            * self.WEIGHTS["ats_compatibility"],
            2,
        )

        recommendation = self._recommend(fit_score)

        return QualificationResult(
            job_id=job.job_id,
            fit_score=fit_score,
            recommendation=recommendation,
            matched_skills=matched,
            missing_skills=missing,
            eliminatory_gaps=[],
            breakdown=breakdown,
            reasoning=[
                f"{len(matched)} requisito(s) técnico(s) compatível(is).",
                f"{len(missing)} requisito(s) técnico(s) não identificado(s).",
                f"Fit calculado: {fit_score}/10.",
            ],
        )

    def _score_seniority(
        self,
        job: JobOpportunity,
        profile: MasterProfile,
    ) -> float:
        title = job.title.lower()

        for seniority in profile.candidate.career_target.seniority:
            if seniority.lower() in title:
                return 10.0

        if "júnior" in title or "junior" in title:
            return 10.0

        return 5.0

    def _score_location(
        self,
        job: JobOpportunity,
        profile: MasterProfile,
    ) -> float:
        preferences = profile.candidate.work_preferences

        if job.work_model.value == "REMOTE" and preferences.remote:
            return 10.0

        if job.work_model.value == "HYBRID" and preferences.hybrid:
            return 10.0

        if job.work_model.value == "ONSITE" and preferences.onsite:
            return 10.0

        if any(
            location.lower() in job.location.lower()
            for location in preferences.preferred_location
        ):
            return 8.0

        return 4.0

    def _recommend(self, fit_score: float) -> str:
        if fit_score >= 7.0:
            return "RECOMENDADA"

        if fit_score >= 6.5:
            return "FILA_SECUNDARIA"

        return "NAO_RECOMENDADA"

from core.schemas.candidate import MasterProfile
from core.schemas.job import JobOpportunity
from core.schemas.personalization import PersonalizationResult
from core.schemas.qualification import QualificationResult


class PersonalizationAgent:
    """Personaliza o posicionamento profissional sem inventar evidências."""

    def personalize(
        self,
        job: JobOpportunity,
        profile: MasterProfile,
        qualification: QualificationResult,
    ) -> PersonalizationResult:
        selected_skills = self._select_skills(
            profile,
            qualification.matched_skills,
        )

        selected_experiences = [
            f"{experience.role} - {experience.company}"
            for experience in profile.experience
        ]

        selected_projects = [
            project.name
            for project in profile.projects
            if self._project_is_relevant(
                project.technologies,
                selected_skills,
            )
        ]

        ats_keywords = sorted(
            {
                requirement
                for requirement in job.requirements
                if requirement.lower()
                in {skill.lower() for skill in selected_skills}
            },
            key=str.lower,
        )

        return PersonalizationResult(
            job_id=job.job_id,
            professional_title=self._build_title(job, profile),
            professional_summary=profile.professional_positioning.summary,
            selected_skills=selected_skills,
            selected_experiences=selected_experiences,
            selected_projects=selected_projects,
            ats_keywords=ats_keywords,
            unsupported_requirements=qualification.missing_skills,
            evidence_verified=True,
        )

    def _select_skills(
        self,
        profile: MasterProfile,
        matched_skills: list[str],
    ) -> list[str]:
        all_skills = (
            profile.skills.core
            + profile.skills.database
            + profile.skills.python
            + profile.skills.analytics
            + profile.skills.tools
            + profile.skills.automation
        )

        matched = {skill.lower() for skill in matched_skills}

        return [
            skill
            for skill in all_skills
            if skill.lower() in matched
        ]

    def _project_is_relevant(
        self,
        technologies: list[str],
        selected_skills: list[str],
    ) -> bool:
        technologies_normalized = {
            technology.lower()
            for technology in technologies
        }

        selected_normalized = {
            skill.lower()
            for skill in selected_skills
        }

        return bool(technologies_normalized & selected_normalized)

    def _build_title(
        self,
        job: JobOpportunity,
        profile: MasterProfile,
    ) -> str:
        target_roles = {
            role.lower()
            for role in profile.candidate.career_target.primary_roles
        }

        if job.title.lower() in target_roles:
            return job.title

        return profile.professional_positioning.title

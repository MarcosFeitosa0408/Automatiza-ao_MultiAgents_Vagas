from datetime import datetime, timezone

from core.repositories.factory import (
    create_job_application_repository,
)
from core.schemas.job_application import JobApplicationObject
from agents.agent_00_memory.memory_agent import MemoryAgent
from agents.agent_01_discovery.discovery_agent import DiscoveryAgent
from agents.agent_02_qualification.qualification_agent import QualificationAgent
from agents.agent_03_personalization.personalization_agent import PersonalizationAgent
from agents.agent_04_application.application_agent import ApplicationAgent
from agents.agent_05_tracking.tracking_agent import TrackingAgent
from agents.agent_06_followup.followup_agent import FollowUpAgent
from agents.agent_07_optimization.optimization_agent import OptimizationAgent

from core.schemas.application import ApplicationPreparation
from core.schemas.job import JobOpportunity, JobStatus
from core.schemas.personalization import PersonalizationResult
from core.schemas.qualification import QualificationResult
from core.validation.validation_gate import ValidationGate


class JobOrchestrator:
    """Coordena o pipeline de análise e preparação de candidaturas."""

    def __init__(self) -> None:
        self.memory_agent = MemoryAgent()
        self.discovery_agent = DiscoveryAgent()
        self.qualification_agent = QualificationAgent()
        self.personalization_agent = PersonalizationAgent()
        self.validation_gate = ValidationGate()
        self.application_agent = ApplicationAgent()
        self.tracking_agent = TrackingAgent()
        self.followup_agent = FollowUpAgent()
        self.optimization_agent = OptimizationAgent()
        self.job_application_repository = create_job_application_repository()


    def _update_job_application(
        self,
        application: JobApplicationObject,
        **updates,
    ) -> JobApplicationObject:
        """Atualiza o objeto central e renova o timestamp de modificação."""

        return application.model_copy(
            update={
                **updates,
                "updated_at": datetime.now(timezone.utc),
            }
        )

    
    def run(
        self,
        jobs: list[JobOpportunity],
    ) -> list[QualificationResult]:
        """Executa Memory -> Discovery -> Qualification."""

        profile = self.memory_agent.load_profile()
        discovered_jobs = self.discovery_agent.discover(jobs)

        results = [
            self.qualification_agent.calculate_fit(job, profile)
            for job in discovered_jobs
        ]

        return sorted(
            results,
            key=lambda result: result.fit_score,
            reverse=True,
        )

    def personalize_job(
        self,
        job: JobOpportunity,
        qualification: QualificationResult,
    ) -> PersonalizationResult:
        """Executa a personalização de uma vaga qualificada."""

        profile = self.memory_agent.get_profile()

        return self.personalization_agent.personalize(
            job,
            profile,
            qualification,
        )

    def prepare_application(
        self,
        job: JobOpportunity,
        qualification: QualificationResult,
    ) -> ApplicationPreparation:
        """
        Personaliza, valida e prepara a candidatura.

        Mesmo quando aprovada pela Validation Gate, a candidatura
        permanece aguardando aprovação humana.
        """

        personalization = self.personalize_job(
            job,
            qualification,
        )

        validation = self.validation_gate.validate(
            qualification,
            personalization,
        )

        return self.application_agent.prepare(
            job_id=job.job_id,
            approved_for_human_review=validation[
                "approved_for_human_review"
            ],
            blocking_issues=validation["blocking_issues"],
            warnings=validation["warnings"],
        )


    def approve_application(
        self,
        preparation: ApplicationPreparation,
    ) -> ApplicationPreparation:
        """Registra a aprovação humana de uma candidatura preparada."""

        return self.application_agent.approve(
            preparation
        )


    def reject_application(
        self,
        preparation: ApplicationPreparation,
    ) -> ApplicationPreparation:
        """Registra a rejeição humana de uma candidatura preparada."""

        return self.application_agent.reject(
            preparation
        )


    def start_tracking(
        self,
        preparation: ApplicationPreparation,
    ):
        """Inicia o acompanhamento de uma candidatura pronta."""

        if not preparation.ready_to_apply:
            raise ValueError(
                "A candidatura precisa estar pronta antes do acompanhamento."
            )

        return self.tracking_agent.start_tracking(
            job_id=preparation.job_id,
        )


    def update_tracking_status(
        self,
        tracking,
        new_status,
        note: str = "",
    ):
        """Atualiza o status de uma candidatura em acompanhamento."""

        return self.tracking_agent.update_status(
            tracking,
            new_status,
            note,
        )
        

    def should_follow_up(
        self,
        tracking,
        followup_count: int,
        last_contact_at,
        now=None,
    ) -> bool:
        """Verifica se uma candidatura está apta para follow-up."""

        return self.followup_agent.should_follow_up(
            tracking=tracking,
            followup_count=followup_count,
            last_contact_at=last_contact_at,
            now=now,
        )


    def calculate_optimization_metrics(
        self,
        applications,
    ) -> dict:
        """Calcula métricas reais do funil de candidaturas."""

        return self.optimization_agent.calculate_metrics(
            applications
        )


    def create_job_application(
        self,
        job: JobOpportunity,
        application_id: str,
    ) -> JobApplicationObject:
        """Cria o objeto central de uma oportunidade no pipeline."""

        return JobApplicationObject(
            application_id=application_id,
            job=job,
        )


    def qualify_job_application(
        self,
        application: JobApplicationObject,
    ) -> JobApplicationObject:
        """Calcula a qualificação e atualiza o objeto central."""

        profile = self.memory_agent.get_profile()

        qualification = self.qualification_agent.calculate_fit(
            application.job,
            profile,
        )

        return self._update_job_application(
             application,
             qualification=qualification,
        )


    def personalize_job_application(
        self,
        application: JobApplicationObject,
    ) -> JobApplicationObject:
        """Personaliza a candidatura e atualiza o objeto central."""

        if application.qualification is None:
            raise ValueError(
                "A candidatura precisa estar qualificada antes da personalização."
            )

        profile = self.memory_agent.get_profile()

        personalization = self.personalization_agent.personalize(
            application.job,
            profile,
            application.qualification,
        )

        return self._update_job_application(
             application,
             personalization=personalization,
        )


    def prepare_job_application(
        self,
        application: JobApplicationObject,
    ) -> JobApplicationObject:
        """Valida e prepara o objeto central para aprovação humana."""

        if application.qualification is None:
            raise ValueError(
                "A candidatura precisa estar qualificada antes da preparação."
            )

        if application.personalization is None:
            raise ValueError(
                "A candidatura precisa estar personalizada antes da preparação."
            )

        validation = self.validation_gate.validate(
            application.qualification,
            application.personalization,
        )

        preparation = self.application_agent.prepare(
            job_id=application.job.job_id,
            approved_for_human_review=validation[
                "approved_for_human_review"
            ],
            blocking_issues=validation["blocking_issues"],
            warnings=validation["warnings"],
        )

        return self._update_job_application(
            application,
            preparation=preparation,
        )


    def approve_job_application(
        self,
        application: JobApplicationObject,
    ) -> JobApplicationObject:
        """Registra a aprovação humana no objeto central."""

        if application.preparation is None:
            raise ValueError(
                "A candidatura precisa estar preparada antes da aprovação."
            )

        approved_preparation = self.application_agent.approve(
            application.preparation
        )

        return self._update_job_application(
            application,
            preparation=approved_preparation,
        )

    def reject_job_application(
        self,
        application: JobApplicationObject,
    ) -> JobApplicationObject:
        """Registra a rejeição humana no objeto central."""

        if application.preparation is None:
            raise ValueError(
                "A candidatura precisa estar preparada antes da rejeição."
            )

        rejected_preparation = self.application_agent.reject(
            application.preparation
        )

        return self._update_job_application(
            application,
            preparation=rejected_preparation,
        )


    def start_job_application_tracking(
        self,
        application: JobApplicationObject,
    ) -> JobApplicationObject:
        """Inicia o acompanhamento da candidatura aprovada."""

        if application.preparation is None:
            raise ValueError(
                "A candidatura precisa estar preparada antes do acompanhamento."
            )

        if not application.preparation.ready_to_apply:
            raise ValueError(
                "A candidatura precisa estar aprovada antes do acompanhamento."
            )

        tracking = self.tracking_agent.start_tracking(
            job_id=application.job.job_id,
        )

        return self._update_job_application(
            application,
            tracking=tracking,
        )


    def update_job_application_status(
        self,
        application: JobApplicationObject,
        new_status,
        note: str = "",
    ) -> JobApplicationObject:
        """Atualiza o status de acompanhamento no objeto central."""

        if application.tracking is None:
            raise ValueError(
                "A candidatura precisa estar em acompanhamento antes da atualização."
            )

        updated_tracking = self.tracking_agent.update_status(
            application.tracking,
            new_status,
            note,
        )

        return self._update_job_application(
            application,
            tracking=updated_tracking, 
        )


    def should_follow_up_job_application(
        self,
        application: JobApplicationObject,
        now=None,
    ) -> bool:
        """Verifica se o objeto central está apto para follow-up."""

        if application.tracking is None:
            raise ValueError(
                "A candidatura precisa estar em acompanhamento antes do follow-up."
            )

        tracking = application.tracking

        if tracking.followup_count > 0:
            last_contact_at = tracking.last_followup_at
        else:
            applied_events = [
                event
                for event in tracking.history
                if event.status == JobStatus.APPLIED
            ]

            if not applied_events:
                raise ValueError(
                    "A candidatura precisa ter sido enviada antes do follow-up."
                )

            last_contact_at = applied_events[-1].occurred_at

        if last_contact_at is None:
            raise ValueError(
                "Não foi possível identificar a data do último contato."
            )

        return self.followup_agent.should_follow_up(
            tracking=tracking,
            followup_count=tracking.followup_count,
            last_contact_at=last_contact_at,
            now=now,
        )

    def register_job_application_follow_up(
        self,
        application: JobApplicationObject,
        occurred_at=None,
    ) -> JobApplicationObject:
        """Registra um follow-up realizado no objeto central."""

        if application.tracking is None:
            raise ValueError(
                "A candidatura precisa estar em acompanhamento antes do follow-up."
            )

        if (
            application.tracking.followup_count
            >= self.followup_agent.MAX_FOLLOWUPS
        ):
            raise ValueError(
                "O limite máximo de follow-ups já foi atingido."
            )

        if application.tracking.current_status not in {
            JobStatus.APPLIED,
            JobStatus.SCREENING,
        }:
            raise ValueError(
                "Follow-up só pode ser registrado em candidatura enviada ou em triagem."
            )

        followup_time = (
            occurred_at
            or datetime.now(timezone.utc)
        )

        if not self.should_follow_up_job_application(
            application,
            now=followup_time,
        ):
            raise ValueError(
                "Ainda não é o momento permitido para registrar o follow-up."
            )

        updated_tracking = application.tracking.model_copy(
            update={
                "followup_count": (
                    application.tracking.followup_count + 1
                ),
                "last_followup_at": followup_time,
            }
        )

        return self._update_job_application(
            application,
            tracking=updated_tracking,
        )
        

    def calculate_job_application_metrics(
        self,
        applications: list[JobApplicationObject],
    ) -> dict:
        """Calcula métricas usando o tracking dos objetos centrais."""

        trackings = [
            application.tracking
            for application in applications
            if application.tracking is not None
        ]

        return self.optimization_agent.calculate_metrics(
            trackings
        )


    def save_job_application(
        self,
        application: JobApplicationObject,
    ) -> JobApplicationObject:
        """Salva ou atualiza uma candidatura no repositório."""

        return self.job_application_repository.save(
            application
        )

    def delete_job_application(
        self,
        application_id: str,
    ) -> bool:
        """Remove uma candidatura armazenada no repositório."""

        return self.job_application_repository.delete(
            application_id
        )

    def get_job_application(
        self,
        application_id: str,
    ) -> JobApplicationObject | None:
        """Busca uma candidatura pelo application_id."""

        return self.job_application_repository.get(
            application_id
        )

    def list_job_applications(
        self,
    ) -> list[JobApplicationObject]:
        """Lista todas as candidaturas armazenadas."""

        return self.job_application_repository.list_all()





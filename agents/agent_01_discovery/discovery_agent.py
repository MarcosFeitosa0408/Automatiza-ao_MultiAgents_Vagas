from collections.abc import Iterable

from agents.agent_01_discovery.sources.base_source import BaseJobSource
from agents.agent_01_discovery.sources.greenhouse_source import GreenhouseJobSource
from core.schemas.job import JobOpportunity


class DiscoveryAgent:
    """Normaliza e consolida vagas descobertas por diferentes fontes."""

    def deduplicate(
        self,
        jobs: Iterable[JobOpportunity],
    ) -> list[JobOpportunity]:
        """Remove vagas duplicadas por ID ou identidade normalizada."""

        unique_jobs: list[JobOpportunity] = []
        seen_job_ids: set[str] = set()
        seen_job_keys: set[tuple[str, str, str, str]] = set()

        for job in jobs:
            normalized_key = (
                job.company.strip().casefold(),
                job.title.strip().casefold(),
                job.location.strip().casefold(),
                job.work_model.value,
            )

            if (
                job.job_id in seen_job_ids
                or normalized_key in seen_job_keys
            ):
                continue

            seen_job_ids.add(job.job_id)
            seen_job_keys.add(normalized_key)
            unique_jobs.append(job)

        return unique_jobs

    def normalize_job(
        self,
        raw_job: dict,
    ) -> JobOpportunity:
        """Converte dados brutos de uma vaga em JobOpportunity validado."""

        return JobOpportunity.model_validate(raw_job)


    def discover_raw(
        self,
        raw_jobs: Iterable[dict],
    ) -> list[JobOpportunity]:
        """Normaliza e remove duplicidades de vagas brutas."""

        normalized_jobs = [
            self.normalize_job(raw_job)
            for raw_job in raw_jobs
        ]

        return self.deduplicate(normalized_jobs)

    def discover_from_source(
        self,
        source: BaseJobSource,
    ) -> list[JobOpportunity]:
        """Coleta e processa vagas fornecidas por uma fonte externa."""

        raw_jobs = source.fetch_jobs()

        return self.discover_raw(raw_jobs)

    def discover_from_sources(
        self,
        sources: Iterable[BaseJobSource],
    ) -> list[JobOpportunity]:
        """Coleta, normaliza e consolida vagas de múltiplas fontes."""

        raw_jobs: list[dict] = []

        for source in sources:
            raw_jobs.extend(source.fetch_jobs())

        return self.discover_raw(raw_jobs)
        
    def discover(
        self,
        jobs: Iterable[JobOpportunity],
    ) -> list[JobOpportunity]:
        """Executa a primeira etapa do pipeline de descoberta."""

        return self.deduplicate(jobs)


    def build_greenhouse_sources(
        self,
        boards: Iterable[dict],
    ) -> list[GreenhouseJobSource]:
        """Cria fontes Greenhouse a partir dos boards configurados."""

        return [
            GreenhouseJobSource(
                board_token=board["board_token"],
                company_name=board["company_name"],
            )
            for board in boards
        ]


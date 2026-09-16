import httpx

from agents.agent_01_discovery.sources.base_source import BaseJobSource


class AdzunaJobSource(BaseJobSource):
    """Fonte de vagas baseada na API da Adzuna."""

    BASE_URL = "https://api.adzuna.com/v1/api/jobs/br/search/1"

    def __init__(
        self,
        app_id: str,
        app_key: str,
        query: str = "",
        location: str = "",
    ):
        self.app_id = app_id
        self.app_key = app_key
        self.query = query
        self.location = location

    def fetch_jobs(self):
        """Coleta vagas da API da Adzuna e normaliza a resposta."""

        response = httpx.get(
            self.BASE_URL,
            params={
                "app_id": self.app_id,
                "app_key": self.app_key,
                "what": self.query,
                "where": self.location,
            },
            timeout=10.0,
        )

        response.raise_for_status()

        return self.normalize_response(
            response.json()
        )

    def normalize_response(
        self,
        api_response: dict,
    ) -> list[dict]:
        """Converte a resposta da Adzuna para o formato bruto da plataforma."""

        jobs: list[dict] = []

        for item in api_response.get("results", []):
            jobs.append(
                {
                    "job_id": str(item["id"]),
                    "title": item["title"],
                    "company": item["company"]["display_name"],
                    "source": "ADZUNA",
                    "url": item.get("redirect_url"),
                    "location": item.get(
                        "location",
                        {},
                    ).get(
                        "display_name",
                        "NAO_IDENTIFICADO",
                    ),
                    "description": item.get("description", ""),
                }
            )

        return jobs

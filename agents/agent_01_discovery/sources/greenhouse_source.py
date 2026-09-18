import httpx

from agents.agent_01_discovery.sources.base_source import BaseJobSource


class GreenhouseJobSource(BaseJobSource):
    """Fonte de vagas baseada na Greenhouse Job Board API."""

    BASE_URL = "https://boards-api.greenhouse.io/v1/boards"

    def __init__(
        self,
        board_token: str,
        company_name: str,
    ):
        self.board_token = board_token
        self.company_name = company_name

    def fetch_jobs(self):
        """Coleta vagas públicas da Greenhouse e normaliza a resposta."""

        url = (
            f"{self.BASE_URL}/"
            f"{self.board_token}/jobs"
        )

        response = httpx.get(
            url,
            params={
                "content": "true",
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
        """Converte a resposta da Greenhouse para o formato da plataforma."""

        jobs: list[dict] = []

        for item in api_response.get("jobs", []):
            jobs.append(
                {
                    "job_id": f"greenhouse-{item['id']}",
                    "title": item["title"],
                    "company": self.company_name,
                    "source": "GREENHOUSE",
                    "url": item.get("absolute_url"),
                    "location": item.get(
                        "location",
                        {},
                    ).get(
                        "name",
                        "NAO_IDENTIFICADO",
                    ),
                    "description": item.get("content", ""),
                }
            )

        return jobs

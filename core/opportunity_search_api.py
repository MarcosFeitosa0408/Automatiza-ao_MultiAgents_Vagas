import os

import httpx
from fastapi import APIRouter, HTTPException

from agents.agent_01_discovery.discovery_agent import DiscoveryAgent
from agents.agent_01_discovery.sources.adzuna_source import AdzunaJobSource
from core.schemas.job import JobOpportunity
from core.schemas.opportunity_search import OpportunitySearchRequest


router = APIRouter(prefix="/opportunities", tags=["Oportunidades"])


@router.post("/search", response_model=list[JobOpportunity])
def search_opportunities(request: OpportunitySearchRequest):
    app_id = os.getenv("ADZUNA_APP_ID", "").strip()
    app_key = os.getenv("ADZUNA_APP_KEY", "").strip()

    if not app_id or not app_key:
        raise HTTPException(
            status_code=503,
            detail="A busca Adzuna ainda não foi configurada no servidor.",
        )

    source = AdzunaJobSource(
        app_id=app_id,
        app_key=app_key,
        query=request.query,
        location=request.location,
        country=request.country,
    )

    try:
        return DiscoveryAgent().discover_from_source(source)
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail="A fonte de vagas demorou para responder. Tente novamente.",
        ) from None
    except httpx.HTTPError:
        raise HTTPException(
            status_code=502,
            detail=(
                "A fonte de vagas não aceitou ou não conseguiu concluir "
                "a consulta. Confira o país e a configuração do servidor."
            ),
        ) from None
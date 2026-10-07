"""Correção humana do anúncio sem apagar etapas externas registradas."""
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field

from core.accounts import get_store
from core.auth_api import require_user
from core.schemas.job import StrictModel
from core.schemas.job_application import JobApplicationObject

router = APIRouter(tags=['Correção de anúncio'])


class JobCorrectionRequest(StrictModel):
    description: str = Field(max_length=50000)
    requirements: list[str] = Field(min_length=1, max_length=100)
    desirable_requirements: list[str] = Field(default_factory=list, max_length=100)
    expected_updated_at: datetime
    confirmed: Literal[True]


@router.patch('/job-applications/{application_id}/correct-details', response_model=JobApplicationObject)
def correct_details(application_id: str, payload: JobCorrectionRequest, user=Depends(require_user)):
    def clean(values):
        result = list(dict.fromkeys(value.strip() for value in values if value.strip()))
        if any(len(value) > 300 for value in result):
            raise HTTPException(422, 'Separe os requisitos em itens curtos. O anúncio completo pertence à descrição.')
        return result

    requirements = clean(payload.requirements)
    desirable = clean(payload.desirable_requirements)
    if not requirements:
        raise HTTPException(422, 'Informe pelo menos um requisito real do anúncio.')
    with get_store().connection() as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT payload FROM private_applications WHERE user_id=? AND application_id=?',
                         (user['id'], application_id)).fetchone()
        if not row:
            raise HTTPException(404, 'Candidatura não encontrada.')
        application = JobApplicationObject.model_validate_json(row['payload'])
        if application.preparation is not None:
            raise HTTPException(409, 'A correção está indisponível para candidaturas com preparação ou aprovação registrada. O conteúdo existente foi preservado.')
        if application.updated_at != payload.expected_updated_at:
            raise HTTPException(409, 'Esta vaga mudou em outra sessão. Atualize a lista e confira os dados antes de corrigir.')
        job = application.job.model_copy(update={
            'description': payload.description.strip(),
            'requirements': requirements,
            'desirable_requirements': desirable,
        })
        updated = application.model_copy(update={
            'job': job, 'qualification': None, 'personalization': None,
            'updated_at': datetime.now(timezone.utc),
        })
        # Mantém IDs, origem, links, acompanhamento, eventos e follow-ups.
        db.execute('UPDATE private_applications SET payload=? WHERE user_id=? AND application_id=?',
                   (updated.model_dump_json(), user['id'], application_id))
    return updated

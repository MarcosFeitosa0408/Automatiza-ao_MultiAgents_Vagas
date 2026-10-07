"""Registros humanos de etapas externas; nunca envia candidaturas."""
from datetime import datetime, timezone
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import Field
from core.accounts import get_store
from core.auth_api import require_user
from core.schemas.job import StrictModel, JobStatus
from core.schemas.job_application import JobApplicationObject
from core.schemas.tracking import ApplicationTracking, TrackingEvent

router=APIRouter(tags=['Acompanhamento humano'])


class ProgressRequest(StrictModel):
    new_status: Literal['APPLIED','SCREENING','INTERVIEW','FINAL','OFFER','HIRED','REJECTED','WITHDRAWN','NO_RESPONSE','APPLICATION_FAILED']
    expected_status: JobStatus | None = None
    confirmed: Literal[True]
    note: str = Field(default='',max_length=1000)


@router.post('/job-applications/{application_id}/progress')
def record_progress(application_id: str, payload: ProgressRequest, user=Depends(require_user)):
    with get_store().connection() as db:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute('SELECT payload FROM private_applications WHERE user_id=? AND application_id=?',(user['id'],application_id)).fetchone()
        if not row:
            raise HTTPException(404,'Candidatura não encontrada.')
        application=JobApplicationObject.model_validate_json(row['payload'])
        tracking=application.tracking
        current=tracking.current_status if tracking else None
        status=JobStatus(payload.new_status)
        # Repetir o último registro após falha de conexão não duplica o histórico.
        if current==status:
            return application
        if current!=payload.expected_status:
            raise HTTPException(409,'A etapa mudou em outra sessão. Atualize a lista antes de registrar.')
        event=TrackingEvent(status=status,note=payload.note.strip() or 'Etapa externa confirmada pela pessoa. Data do registro.')
        if tracking:
            tracking=tracking.model_copy(update={'current_status':status,'history':tracking.history+[event]})
        else:
            tracking=ApplicationTracking(job_id=application.job.job_id,current_status=status,history=[event])
        application=application.model_copy(update={'tracking':tracking,'updated_at':datetime.now(timezone.utc)})
        db.execute('UPDATE private_applications SET payload=? WHERE user_id=? AND application_id=?',(application.model_dump_json(),user['id'],application_id))
    return application

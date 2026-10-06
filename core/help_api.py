"""Ajuda com encaminhamento explícito e histórico exclusivo do administrador."""
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from core.accounts import get_store
from core.auth_api import require_user
from core.admin_api import require_admin
from core.help_knowledge import answer, normalize, suggestions

router = APIRouter(tags=['Ajuda'])
SP = timezone(timedelta(hours=-3))


def period(now=None):
    date = datetime.fromtimestamp(time.time() if now is None else now, SP)
    monday = (date - timedelta(days=date.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    return monday.date().isoformat(), (monday + timedelta(days=7)).isoformat()


class Question(BaseModel):
    model_config = ConfigDict(extra='forbid')
    question: str = Field(min_length=3, max_length=600)

    @field_validator('question')
    @classmethod
    def strip(cls, value):
        value = value.strip()
        if len(value) < 3:
            raise ValueError('Escreva sua dúvida sobre a plataforma.')
        return value


class Forward(Question):
    request_id: UUID


class Review(BaseModel):
    model_config = ConfigDict(extra='forbid')
    state: Literal['pending','reviewing','answered']
    answer: str = Field(default='', max_length=4000)


def quota(store, user):
    week, renews = period()
    with store.connection() as db:
        row = db.execute('SELECT used FROM help_usage WHERE user_id=? AND week=?', (user['id'],week)).fetchone()
    used = row['used'] if row else 0
    return {'remaining': None if user['role']=='admin' else max(0,3-used), 'renews_at':renews, 'week':week}


@router.get('/help')
def help_info(user=Depends(require_user)):
    return {**quota(get_store(),user),'suggestions':suggestions()}


@router.post('/help/ask')
def ask(payload: Question, user=Depends(require_user)):
    text = answer(payload.question)
    return {'known': text is not None, 'answer':text or 'Ainda não tenho uma resposta para essa dúvida. Posso encaminhá-la ao administrador para melhoria.', **quota(get_store(),user)}


@router.post('/help/forward')
def forward(payload: Forward, user=Depends(require_user)):
    if answer(payload.question) is not None:
        raise HTTPException(409,'Esta dúvida já tem uma orientação disponível. Consulte o robô.')
    # Evitar credenciais/contatos em mensagens de suporte; não é detecção perfeita.
    import re
    if re.search(r'@|https?://|postgres(?:ql)?://|\b(?:senha|password|token|chave)\s*[:=]|\b\d{8,}\b',payload.question,re.I):
        raise HTTPException(422,'Retire e-mails, links, números pessoais e segredos antes de encaminhar.')
    store=get_store();week,_=period();question=payload.question;key=normalize(question)
    with store.connection() as db:
        db.execute('BEGIN IMMEDIATE')
        existing=db.execute('SELECT user_id,normalized FROM help_questions WHERE id=?',(str(payload.request_id),)).fetchone()
        if existing:
            if existing['user_id'] != user['id'] or existing['normalized'] != key:
                raise HTTPException(409,'Não foi possível confirmar esse envio. Faça uma nova pergunta.')
            duplicate=True
        same=db.execute('SELECT id FROM help_questions WHERE user_id=? AND week=? AND normalized=?',(user['id'],week,key)).fetchone()
        if existing or same:
            duplicate=True
        else:
            row=db.execute('SELECT used FROM help_usage WHERE user_id=? AND week=?',(user['id'],week)).fetchone()
            used=row['used'] if row else 0
            if user['role']!='admin' and used>=3:
                raise HTTPException(429,'Você já encaminhou 3 dúvidas nesta semana. As orientações conhecidas continuam disponíveis.')
            db.execute('INSERT INTO help_questions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',(str(payload.request_id),user['id'],week,question,key,'pending','',time.time(),time.time()))
            db.execute('INSERT INTO help_usage VALUES (?, ?, ?) ON CONFLICT(user_id,week) DO UPDATE SET used=excluded.used',(user['id'],week,used+1))
            duplicate=False
    return {'sent':True,'duplicate':duplicate,**quota(store,user)}


def query_week(value):
    if value is None:
        return period()[0]
    try:
        parsed=datetime.strptime(value,'%Y-%m-%d')
        if parsed.weekday()!=0:
            raise ValueError()
        return parsed.date().isoformat()
    except ValueError:
        raise HTTPException(422,'Escolha a segunda-feira da semana para consultar.') from None


@router.get('/admin/help/questions')
def history(week: str | None=None, offset: int=0, admin=Depends(require_admin)):
    if offset<0:
        raise HTTPException(422,'Página inválida.')
    week=query_week(week)
    with get_store().connection() as db:
        rows=db.execute('SELECT id,question,normalized,state,answer,created_at FROM help_questions WHERE week=? ORDER BY created_at,id LIMIT 100 OFFSET ?',(week,offset)).fetchall()
        total=db.execute('SELECT COUNT(*) FROM help_questions WHERE week=?',(week,)).fetchone()[0]
    return {'items':[dict(row) for row in rows],'total':total,'week':week}


@router.get('/admin/help/export')
def export(week: str | None=None, admin=Depends(require_admin)):
    week=query_week(week)
    with get_store().connection() as db:
        count=db.execute('SELECT COUNT(*) FROM help_questions WHERE week=?',(week,)).fetchone()[0]
        if count>5000:
            raise HTTPException(413,'O histórico é muito extenso para esta exportação.')
        rows=db.execute('SELECT question,state,answer,created_at FROM help_questions WHERE week=? ORDER BY created_at,id',(week,)).fetchall()
    data={'week':week,'questions':[dict(row) for row in rows]}
    return Response(json.dumps(data,ensure_ascii=False,indent=2),media_type='application/json',headers={'Content-Disposition':f'attachment; filename="duvidas-{week}.json"'})


@router.patch('/admin/help/questions/{question_id}')
def review(question_id: str, payload: Review, admin=Depends(require_admin)):
    if payload.state=='answered' and not payload.answer.strip():
        raise HTTPException(422,'Escreva a resposta revisada antes de marcar como respondida.')
    with get_store().connection() as db:
        result=db.execute('UPDATE help_questions SET state=?,answer=?,updated_at=? WHERE id=?',(payload.state,payload.answer.strip(),time.time(),question_id))
        if not result.rowcount:
            raise HTTPException(404,'Dúvida não encontrada.')
    return {'saved':True}


@router.delete('/admin/help/questions/{question_id}')
def delete(question_id: str, admin=Depends(require_admin)):
    with get_store().connection() as db:
        result=db.execute('DELETE FROM help_questions WHERE id=?',(question_id,))
        if not result.rowcount:
            raise HTTPException(404,'Dúvida não encontrada.')
    return {'deleted':True}

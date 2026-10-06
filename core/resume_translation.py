"""Tradução opcional da cópia do currículo, sem alterar o perfil ou a vaga."""
import json
import os
from typing import Literal

import httpx
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict
from core.resume_preview import ResumePreview


class TranslationRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    language: Literal['en-US', 'es']


class TranslatedResume(ResumePreview):
    language: Literal['en-US', 'es']


def translate_resume(preview: ResumePreview, language: str) -> TranslatedResume:
    if language not in ('en-US', 'es'):
        raise HTTPException(422, 'Escolha inglês ou espanhol.')
    key = os.getenv('DEEPL_API_KEY', '').strip()
    if not key:
        raise HTTPException(503, 'A tradução ainda não foi configurada no servidor.')
    result = preview.model_dump(mode='json')
    slots = []

    def select(container, field):
        value = container[field]
        if isinstance(value, str) and value.strip():
            slots.append((container, field, value))

    for field in ('professional_title', 'professional_summary'):
        select(result, field)
    for index in range(len(result['skills'])):
        select(result['skills'], index)
    for item in result['education']:
        for field in ('degree', 'status'):
            select(item, field)
    for item in result['experience']:
        select(item, 'role')
        for index in range(len(item['responsibilities'])):
            select(item['responsibilities'], index)
        for achievement in item['achievements']:
            select(achievement, 'description')
    for item in result['projects']:
        select(item, 'description')
    for field in result['languages']:
        select(result['languages'], field)

    # Deduplicar economiza a cota; identificadores, contatos, nomes e datas
    # não entram nos campos selecionados. Texto livre pode conter dados pessoais.
    texts = list(dict.fromkeys(value for _, _, value in slots))
    if sum(map(len, texts)) > 20000:
        raise HTTPException(413, 'O currículo é muito extenso para tradução. Reduza os textos e tente novamente.')
    batches = [texts[index:index + 50] for index in range(0, len(texts), 50)]
    bodies = [{'text': batch, 'source_lang': 'PT', 'target_lang': language.upper(), 'preserve_formatting': True} for batch in batches]
    if any(len(json.dumps(body, ensure_ascii=False).encode('utf-8')) > 120000 for body in bodies):
        raise HTTPException(413, 'O currículo é muito extenso para tradução.')
    endpoint = 'https://api-free.deepl.com/v2/translate' if key.endswith(':fx') else 'https://api.deepl.com/v2/translate'
    translated = {}
    try:
        with httpx.Client(timeout=30, follow_redirects=False) as client:
            for batch, body in zip(batches, bodies):
                response = client.post(endpoint, headers={'Authorization': 'DeepL-Auth-Key ' + key}, json=body)
                if response.status_code == 456:
                    raise HTTPException(503, 'A cota do serviço de tradução acabou. O currículo em português continua disponível.')
                if response.status_code == 429:
                    raise HTTPException(429, 'O serviço de tradução está ocupado. Aguarde e tente novamente.')
                if response.status_code != 200:
                    raise HTTPException(502, 'Não foi possível traduzir agora. Tente novamente mais tarde.')
                items = response.json()['translations']
                if len(items) != len(batch) or any(not isinstance(item.get('text'), str) or not item['text'].strip() for item in items):
                    raise ValueError('Resposta incompleta.')
                translated.update(zip(batch, [item['text'] for item in items]))
    except HTTPException:
        raise
    except (httpx.HTTPError, ValueError, KeyError, TypeError, AttributeError):
        raise HTTPException(502, 'Não foi possível traduzir agora. Seu currículo original foi preservado.') from None
    for container, field, value in slots:
        container[field] = translated[value]
    result['warnings'].append('Tradução automática: revise termos, números e descrições antes de enviar à empresa.')
    return TranslatedResume.model_validate({**result, 'language': language})

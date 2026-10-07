"""Identifica a mesma oportunidade sem comparar apenas cargo e empresa."""
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from fastapi import HTTPException


def canonical_url(value):
    if not value:
        return None
    parts = urlsplit(str(value))
    # Preserva parâmetros e fragmentos que podem identificar vagas.
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.casefold().startswith('utm_') and k.casefold() not in ('gclid', 'fbclid', 'msclkid')]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path or '/', urlencode(sorted(query)), parts.fragment))


def same_opportunity(left, right):
    same_source_id = (left.source.strip().casefold(), left.job_id.strip()) == (right.source.strip().casefold(), right.job_id.strip())
    left_url = canonical_url(left.url)
    return same_source_id or bool(left_url and left_url == canonical_url(right.url))


def duplicate_error(application):
    return HTTPException(409, detail={
        'code': 'opportunity_already_saved',
        'message': 'Esta vaga já está nas suas candidaturas.',
        'application_id': application.application_id,
        'title': application.job.title,
        'company': application.job.company,
    })

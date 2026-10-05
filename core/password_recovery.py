"""Recuperação por e-mail: tokens com hash, 30 minutos e consumo transacional."""
import hashlib
import logging
import os
import re
import secrets
import time
from urllib.parse import urlsplit

import httpx
from fastapi import HTTPException
from core.accounts import password_hash

logger = logging.getLogger(__name__)


def mail_settings():
    key = os.getenv('BREVO_API_KEY', '').strip()
    sender = os.getenv('RECOVERY_FROM_EMAIL', '').strip()
    origin = os.getenv('PUBLIC_APP_URL', '').strip().rstrip('/')
    parsed = urlsplit(origin)
    if (not key or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', sender)
            or parsed.scheme != 'https' or not parsed.hostname
            or parsed.username or parsed.password or parsed.query or parsed.fragment
            or parsed.path not in ('', '/')):
        raise HTTPException(503, 'Recuperação por e-mail ainda não configurada. Entre em contato com o responsável pela plataforma.')
    return key, sender, origin


def send_recovery_email(email, token, settings):
    key, sender, origin = settings
    link = origin + '/#/redefinir-senha?token=' + token
    with httpx.Client(timeout=15) as client:
        response = client.post('https://api.brevo.com/v3/smtp/email',
            headers={'api-key': key, 'accept': 'application/json'},
            json={'sender': {'name': 'MultiAgents Vagas', 'email': sender},
                  'to': [{'email': email}], 'subject': 'Redefinir senha — MultiAgents Vagas',
                  'textContent': 'Você solicitou uma nova senha. Abra este link em até 30 minutos:\n' + link
                      + '\n\nSe não foi você, ignore esta mensagem. Sua senha permanece a mesma. Nunca compartilhe este link.'})
        response.raise_for_status()


def deliver_recovery(store, email, settings):
    token = secrets.token_urlsafe(48)
    digest = hashlib.sha256(token.encode()).hexdigest()
    try:
        with store.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('DELETE FROM password_resets WHERE expires_at<=?', (time.time(),))
            user = db.execute('SELECT id FROM users WHERE email=?', (email,)).fetchone()
            if not user:
                return
            db.execute('INSERT INTO password_resets VALUES (?, ?, ?)', (digest, user['id'], time.time() + 1800))
        try:
            send_recovery_email(email, token, settings)
        except Exception:
            with store.connection() as db:
                db.execute('DELETE FROM password_resets WHERE token_hash=?', (digest,))
            raise
    except Exception:
        # Não registrar exceção do provedor: ela pode conter URL, e-mail ou credencial.
        logger.error('Não foi possível entregar um e-mail de recuperação. Confira a configuração do serviço de e-mail.')


def reset_password(store, token, password):
    digest = hashlib.sha256(token.encode()).hexdigest()
    hashed = password_hash.hash(password)
    with store.connection() as db:
        db.execute('BEGIN IMMEDIATE')
        row = db.execute('SELECT user_id FROM password_resets WHERE token_hash=? AND expires_at>?', (digest, time.time())).fetchone()
        if not row:
            raise HTTPException(400, 'Link inválido ou expirado. Solicite outro link em Esqueci minha senha.')
        db.execute('UPDATE users SET password_hash=? WHERE id=?', (hashed, row['user_id']))
        db.execute('DELETE FROM sessions WHERE user_id=?', (row['user_id'],))
        db.execute('DELETE FROM password_resets WHERE user_id=?', (row['user_id'],))
    return {'message': 'Senha atualizada com sucesso. Entre com sua nova senha. A autorização de acesso permanece a mesma.'}

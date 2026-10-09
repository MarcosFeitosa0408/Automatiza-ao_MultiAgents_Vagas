from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator
from core.accounts import get_store

router = APIRouter(prefix='/auth', tags=['Conta'])
bearer = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    email: str = Field(min_length=3, max_length=254)
    password: SecretStr = Field(min_length=8, max_length=128)

    @field_validator('email')
    @classmethod
    def normalize_email(cls, value):
        import re
        value = value.strip().casefold()
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value):
            raise ValueError('Informe um e-mail válido.')
        return value


class RegisterRequest(LoginRequest):
    name: str = Field(min_length=1, max_length=100)

    @field_validator('name')
    @classmethod
    def trim_name(cls, value):
        value = value.strip()
        if not value:
            raise ValueError('Informe seu nome.')
        return value


def require_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
):
    if not credentials or credentials.scheme.casefold() != 'bearer':
        raise HTTPException(401, 'Entre na sua conta para continuar.', headers={'WWW-Authenticate': 'Bearer'})

    store = get_store()
    user = store.current_user(credentials.credentials)
    route = request.scope.get('route')
    route_path = getattr(route, 'path', request.url.path)

    # Entrada, ajuda e controles administrativos mantêm suas proteções próprias.
    if request.url.path.startswith(('/auth/', '/help/', '/admin/')):
        return user

    from core.subscriptions import SubscriptionStore
    status = SubscriptionStore(store).status(user['id'])

    if status['access_allowed']:
        return user

    consultation_routes = {
        '/profile',
        '/job-applications',
        '/job-applications/metrics',
        '/job-applications/{application_id}',
    }
    if (
        status['read_allowed']
        and request.method == 'GET'
        and route_path in consultation_routes
    ):
        return user

    raise HTTPException(
        402,
        detail={
            'code': 'subscription_required',
            'message': 'Ative seu plano para utilizar esta função. Seu perfil e histórico permanecem salvos.',
            'subscription': status,
        },
    )


def session_result(store, user):
    return {'user': user, 'access_token': store.issue_session(user['id']), 'token_type': 'bearer', 'expires_in': 28800}


@router.post('/register', status_code=201)
def register(payload: RegisterRequest, request: Request):
    store = get_store()
    store.limit('register:' + (request.client.host if request.client else 'unknown'), 10)
    store.create_user(payload.name, payload.email, payload.password.get_secret_value())
    return {'pending_approval': True, 'message': 'Conta criada. Aguarde a autorização do administrador.'}


@router.post('/register-trial', status_code=201)
def register_trial(payload: RegisterRequest, request: Request):
    store = get_store()
    store.limit(
        'register:' + (request.client.host if request.client else 'unknown'),
        10,
    )
    user = store.create_user(
        payload.name,
        payload.email,
        payload.password.get_secret_value(),
        commercial=True,
    )
    return session_result(store, user)


@router.post('/login')
def login(payload: LoginRequest, request: Request):
    store = get_store()
    store.limit('login:' + (request.client.host if request.client else 'unknown'))
    user = store.check_password(payload.email, payload.password.get_secret_value())
    return session_result(store, user)


@router.get('/me')
def me(user=Depends(require_user)):
    return user


@router.post('/logout')
def logout(user=Depends(require_user), credentials=Depends(bearer)):
    get_store().revoke(credentials.credentials)
    return {'logged_out': True}


class RecoveryRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    email: str = Field(min_length=3, max_length=254)
    normalize_email = field_validator('email')(LoginRequest.normalize_email.__func__)


class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    token: SecretStr = Field(min_length=64, max_length=64)
    password: SecretStr = Field(min_length=8, max_length=128)


@router.post('/forgot-password', status_code=202)
def forgot_password(payload: RecoveryRequest, request: Request, background: BackgroundTasks):
    import hashlib
    from core.password_recovery import mail_settings, deliver_recovery
    store = get_store()
    store.limit('recovery-ip:' + (request.client.host if request.client else 'unknown'), 10)
    store.limit('recovery-email:' + hashlib.sha256(payload.email.encode()).hexdigest(), 3)
    settings = mail_settings()
    background.add_task(deliver_recovery, store, payload.email, settings)
    return {'message': 'Se houver uma conta com esse e-mail, você receberá um link de recuperação. Confira também a pasta de spam. O link vale por 30 minutos.'}


@router.post('/reset-password')
def change_forgotten_password(payload: ResetPasswordRequest, request: Request):
    from core.password_recovery import reset_password
    store = get_store()
    store.limit('reset-ip:' + (request.client.host if request.client else 'unknown'), 10)
    return reset_password(store, payload.token.get_secret_value(), payload.password.get_secret_value())

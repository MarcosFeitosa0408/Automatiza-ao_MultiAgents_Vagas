from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator
from core.accounts import get_store

router = APIRouter(prefix='/auth', tags=['Conta'])
bearer = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    email: str = Field(min_length=3, max_length=254)
    password: SecretStr = Field(min_length=15, max_length=128)

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


def require_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    if not credentials or credentials.scheme.casefold() != 'bearer':
        raise HTTPException(401, 'Entre na sua conta para continuar.', headers={'WWW-Authenticate': 'Bearer'})
    return get_store().current_user(credentials.credentials)


def session_result(store, user):
    return {'user': user, 'access_token': store.issue_session(user['id']), 'token_type': 'bearer', 'expires_in': 28800}


@router.post('/register', status_code=201)
def register(payload: RegisterRequest, request: Request):
    store = get_store()
    store.limit('register:' + (request.client.host if request.client else 'unknown'), 10)
    store.create_user(payload.name, payload.email, payload.password.get_secret_value())
    return {'pending_approval': True, 'message': 'Conta criada. Aguarde a autorização do administrador.'}


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

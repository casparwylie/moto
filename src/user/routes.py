from fastapi import FastAPI, Response, APIRouter, Header

from src.user.validation import (
  invalid_username,
  invalid_email,
  invalid_password,
)
from src.user.models import (
  SignUpRequest,
  SignUpResponse,
  LoginRequest,
  LoginResponse,
  LogoutResponse,
  UserDataResponse,
)
from src.user.service import (
  signup,
  login,
  delete_session,
  get_user_by_token,
  check_user_exists,
)


router = APIRouter(prefix='/api/user')

_SESSION_KEY_NAME = 'session_token'
_SESSION_EXPIRE = 10#86400 * 7 * 2 # 2 weeks


def get_token_from_cookie(cookie: Header):
  if cookie:
    parts = cookie.split('=')
    return parts[1] if parts[0] == _SESSION_KEY_NAME else None


@router.get('')
async def get_user(cookie = Header(None)) -> UserDataResponse | None:
  token = get_token_from_cookie(cookie)
  if token and (user := get_user_by_token(token)):
    return UserDataResponse.from_db(user)


@router.post('/signup')
async def signup_user(request: SignUpRequest) -> SignUpResponse | None:
  errors = []
  if err := invalid_username(request.username):
    errors.append(err)
  if err := invalid_password(request.password):
    errors.append(err)
  if err := invalid_email(request.email):
    errors.append(err)
  if exists_type := check_user_exists(request.username, request.email):
    errors.append(
      f'{exists_type.capitalize()} already in use. Please use another.'
    )

  if any(errors):
    return SignUpResponse(
      success=False,
      errors=errors,
    )

  signup(request.username, request.password, request.email)
  return SignUpResponse(success=True, errors=[])


@router.post('/login')
async def login_user(
  request: LoginRequest,
  response: Response,
) -> LoginResponse | None:
  if token := login(request.username, request.password, _SESSION_EXPIRE):
    response.set_cookie(
      key=_SESSION_KEY_NAME,
      value=token,
      expires=_SESSION_EXPIRE,
    )
    return LoginResponse(success=True)
  return LoginResponse(success=False)


@router.get('/logout')
async def logout_user(response: Response, cookie = Header(None)) -> None:
  token = get_token_from_cookie(cookie)
  if token and get_user_by_token(token):
    delete_session(token)
    response.delete_cookie(_SESSION_KEY_NAME)
    return LogoutResponse(success=True)
  return LogoutResponse(success=False)

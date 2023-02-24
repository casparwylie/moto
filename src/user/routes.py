from fastapi import FastAPI, Response, APIRouter, Header

from src.user.validation import (
  invalid_username,
  invalid_email,
  invalid_password,
)
from src.user.models import (
  SignUpRequest,
  SuccessResponse,
  LoginRequest,
  UserDataResponse,
  UserGarageResponse,
  GarageItem,
  SuccessResponse,
  ChangePasswordRequest,
  DeleteGarageItemRequest,
  EditUserFieldRequest,
)
from src.user.service import (
  signup,
  login,
  change_password,
  delete_session,
  get_user_by_token,
  check_user_exists,
  get_user_garage,
  add_user_garage_item,
  delete_user_garage_item,
  edit_user_field,
)


router = APIRouter(prefix='/api/user')

_SESSION_KEY_NAME = 'session_token'
_SESSION_EXPIRE = 86400 * 7 * 2 # 2 weeks


def _get_token_from_cookie(cookie: str | None) -> str | None:
  if cookie:
    parts = cookie.split('=')
    return parts[1] if parts[0] == _SESSION_KEY_NAME else None


@router.get('')
async def get_user(cookie = Header(None)) -> UserDataResponse | None:
  token = _get_token_from_cookie(cookie)
  if token and (user := get_user_by_token(token)):
    return UserDataResponse.from_db(user)


##############
### PUBLIC ###
##############

@router.post('/signup')
async def signup_user(request: SignUpRequest) -> SuccessResponse | None:
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
    return SuccessResponse(
      success=False,
      errors=errors,
    )

  signup(request.username, request.password, request.email)
  return SuccessResponse(success=True, errors=[])


@router.post('/login')
async def login_user(
  request: LoginRequest,
  response: Response,
) -> SuccessResponse | None:
  if token := login(request.username, request.password, _SESSION_EXPIRE):
    response.set_cookie(
      key=_SESSION_KEY_NAME,
      value=token,
      expires=_SESSION_EXPIRE,
    )
    return SuccessResponse(success=True)
  return SuccessResponse(success=False)


@router.get('/garage')
async def get_garage(user_id: int) -> UserGarageResponse | None:
  return UserGarageResponse.from_db(get_user_garage(user_id))


#################
### AUTH ONLY ###
#################

@router.get('/logout')
async def logout_user(response: Response, cookie = Header(None)) -> None:
  token = _get_token_from_cookie(cookie)
  if token and get_user_by_token(token):
    delete_session(token)
    response.delete_cookie(_SESSION_KEY_NAME)
    return SuccessResponse(success=True)
  return SuccessResponse(success=False)


@router.post('/change-password')
async def change_password_user(
  request: ChangePasswordRequest, cookie = Header(None),
) -> SuccessResponse | None:

  token = _get_token_from_cookie(cookie)
  if not (user := get_user_by_token(token)):
    return SuccessResponse(success=False)

  errors = []
  if err := invalid_password(request.new):
    errors.append(err)
  if any(errors):
    return SuccessResponse(
      success=False,
      errors=errors,
    )
  if (
    not (success := change_password(
      user.username,
      request.old,
      request.new
    )
  )):
    errors.append('Incorrect current password.')
  return SuccessResponse(success=success, errors=errors)


@router.post('/edit')
async def edit_field_user(
  request: EditUserFieldRequest, cookie = Header(None),
) -> SuccessResponse | None:

  token = _get_token_from_cookie(cookie)
  if not (user := get_user_by_token(token)):
    return SuccessResponse(success=False)

  errors = []
  validators = {
    'username': invalid_username, 'email': invalid_email,
  }
  if validator := validators.get(request.field):
    if err := validator(request.value):
      errors.append(err)
  else:
      errors.append('Field unknown')

  if request.field == 'username' and check_user_exists(request.value, ''):
    errors.append(
      'Username already in use. Please use another.'
    )
  elif request.field == 'email' and check_user_exists('', request.value):
    errors.append(
      'Email already in use. Please use another.'
    )
  if errors:
    return SuccessResponse(success=False, errors=errors)
  success = edit_user_field(user.id, request.field, request.value)
  return SuccessResponse(success=success)


@router.post('/garage')
async def add_garage_item(
  item: GarageItem, cookie = Header(None)
) -> SuccessResponse:
  token = _get_token_from_cookie(cookie)
  if user := get_user_by_token(token):
    success = add_user_garage_item(
      user_id=user.id,
      make=item.make_name,
      model=item.name,
      year=item.year,
      relation=item.relation,
    )
    return SuccessResponse(success=success)
  return SuccessResponse(success=False)


@router.post('/garage/delete')
async def delete_garage_item(
  request: DeleteGarageItemRequest, cookie = Header(None),
) -> SuccessResponse:
  token = _get_token_from_cookie(cookie)
  if user := get_user_by_token(token):
    success = delete_user_garage_item(
      user_id=user.id, model_id=request.model_id,
    )
    return SuccessResponse(success=success)
  return SuccessResponse(success=False)

from fastapi import Depends, FastAPI, Response, APIRouter, Header
from sqlalchemy import Row

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


router = APIRouter(prefix="/api/user")

_SESSION_KEY_NAME = "session_token"
_SESSION_EXPIRE = 86400 * 7 * 2  # 2 weeks


class NotAuthenticatedException(Exception):
    ...


def _get_token_from_cookie(cookie: str | None) -> str | None:
    if cookie:
        parts = cookie.split("=")
        return parts[1] if parts[0] == _SESSION_KEY_NAME else None


def auth_required(cookie: str = Header(None)) -> Row:
    if token := _get_token_from_cookie(cookie):
        if user := get_user_by_token(token):
            return user
    raise NotAuthenticatedException


##############
### PUBLIC ###
##############


@router.post("/signup")
async def signup_user(request: SignUpRequest) -> SuccessResponse:
    errors = []
    if err := invalid_username(request.username):
        errors.append(err)
    if err := invalid_password(request.password):
        errors.append(err)
    if err := invalid_email(request.email):
        errors.append(err)
    if exists_type := check_user_exists(request.username, request.email):
        errors.append(f"{exists_type.capitalize()} already in use. Please use another.")

    if any(errors):
        return SuccessResponse(
            success=False,
            errors=errors,
        )

    signup(request.username, request.password, request.email)
    return SuccessResponse(success=True, errors=[])


@router.post("/login")
async def login_user(
    request: LoginRequest,
    response: Response,
) -> SuccessResponse:
    if token := login(request.username, request.password, _SESSION_EXPIRE):
        response.set_cookie(
            key=_SESSION_KEY_NAME,
            value=token,
            expires=_SESSION_EXPIRE,
        )
        return SuccessResponse(success=True)
    return SuccessResponse(success=False)


@router.get("/garage")
async def get_garage(user_id: int) -> UserGarageResponse:
    return UserGarageResponse.from_db(get_user_garage(user_id))


#################
### AUTH ONLY ###
#################


@router.get("")
async def get_user(user=Depends(auth_required)) -> UserDataResponse:
    return UserDataResponse.from_db(user)


@router.get("/logout")
async def logout_user(
    response: Response,
    cookie: str = Header(None),
) -> SuccessResponse:
    if token := _get_token_from_cookie(cookie):
        delete_session(token)
        response.delete_cookie(_SESSION_KEY_NAME)
        return SuccessResponse(success=True)
    return SuccessResponse(success=False)


@router.post("/change-password")
async def change_password_user(
    request: ChangePasswordRequest,
    user=Depends(auth_required),
) -> SuccessResponse:
    errors = []
    if err := invalid_password(request.new):
        errors.append(err)
    if any(errors):
        return SuccessResponse(
            success=False,
            errors=errors,
        )
    if not (success := change_password(user.username, request.old, request.new)):
        errors.append("Incorrect current password.")
    return SuccessResponse(success=success, errors=errors)


@router.post("/edit")
async def edit_field_user(
    request: EditUserFieldRequest,
    user=Depends(auth_required),
) -> SuccessResponse:
    errors = []
    validators = {
        "username": invalid_username,
        "email": invalid_email,
    }
    if validator := validators.get(request.field):
        if err := validator(request.value):
            errors.append(err)
    else:
        errors.append("Field unknown")

    if request.field == "username" and check_user_exists(request.value, ""):
        errors.append("Username already in use. Please use another.")
    elif request.field == "email" and check_user_exists("", request.value):
        errors.append("Email already in use. Please use another.")
    if errors:
        return SuccessResponse(success=False, errors=errors)
    success = edit_user_field(user.id, request.field, request.value)
    return SuccessResponse(success=success)


@router.post("/garage")
async def add_garage_item(
    item: GarageItem,
    user=Depends(auth_required),
) -> SuccessResponse:
    success = add_user_garage_item(
        user_id=user.id,
        make=item.make_name,
        model=item.name,
        year=item.year,
        relation=item.relation,
    )
    return SuccessResponse(success=success)


@router.post("/garage/delete")
async def delete_garage_item(
    request: DeleteGarageItemRequest,
    user=Depends(auth_required),
) -> SuccessResponse:
    success = delete_user_garage_item(user_id=user.id, model_id=request.model_id)
    return SuccessResponse(success=success)

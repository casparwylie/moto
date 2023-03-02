from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, Response, status
from sqlalchemy import Row

from src.auth import SESSION_KEY_NAME, auth_required, get_token
from src.user.models import (
    ChangePasswordRequest,
    DeleteGarageItemRequest,
    EditUserFieldRequest,
    ForgotPasswordRequest,
    GarageItem,
    LoginRequest,
    SignUpRequest,
    SuccessResponse,
    UserDataResponse,
    UserGarageResponse,
)
from src.user.service import (
    add_user_garage_item,
    change_password,
    check_user_exists,
    delete_session,
    delete_user_garage_item,
    edit_user_field,
    get_user_by_token,
    get_user_garage,
    login,
    signup,
)
from src.user.validation import invalid_email, invalid_password, invalid_username

router = APIRouter(prefix="/api/user")

_SESSION_EXPIRE = 86400 * 7 * 2  # 2 weeks


##############
### PUBLIC ###
##############


@router.post("/signup")
async def _signup_user(request: SignUpRequest) -> SuccessResponse:
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
async def _login_user(
    request: LoginRequest,
    response: Response,
) -> SuccessResponse:
    if token := login(request.username, request.password, _SESSION_EXPIRE):
        response.set_cookie(
            key=SESSION_KEY_NAME,
            value=token,
            expires=_SESSION_EXPIRE,
        )
        return SuccessResponse(success=True)
    return SuccessResponse(success=False)


@router.get("/garage")
async def _get_garage(user_id: int) -> UserGarageResponse:
    return UserGarageResponse.from_db(get_user_garage(user_id))


@router.post("/forgot-password")
async def _forgot_password(
    request: ForgotPasswordRequest,
) -> SuccessResponse:
    return SuccessResponse(success=True)


#################
### AUTH ONLY ###
#################


@router.get("")
async def _get_user(user: Row = Depends(auth_required)) -> UserDataResponse:
    return UserDataResponse.from_db(user)


@router.get("/logout")
async def _logout_user(
    response: Response,
    token: None | str = Depends(get_token),
) -> SuccessResponse:
    if token:
        delete_session(token)
        response.delete_cookie(SESSION_KEY_NAME)
        return SuccessResponse(success=True)
    return SuccessResponse(success=False)


@router.post("/change-password")
async def _change_password_user(
    request: ChangePasswordRequest,
    user: Row = Depends(auth_required),
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
async def _edit_field_user(
    request: EditUserFieldRequest,
    user: Row = Depends(auth_required),
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
        raise HTTPException(status.HTTP_403_FORBIDDEN)

    if request.field == "username" and check_user_exists(request.value, ""):
        errors.append("Username already in use. Please use another.")
    elif request.field == "email" and check_user_exists("", request.value):
        errors.append("Email already in use. Please use another.")
    if errors:
        return SuccessResponse(success=False, errors=errors)
    success = edit_user_field(user.id, request.field, request.value)
    return SuccessResponse(success=success)


@router.post("/garage")
async def _add_garage_item(
    item: GarageItem,
    user: Row = Depends(auth_required),
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
async def _delete_garage_item(
    request: DeleteGarageItemRequest,
    user: Row = Depends(auth_required),
) -> SuccessResponse:
    success = delete_user_garage_item(user_id=user.id, model_id=request.model_id)
    return SuccessResponse(success=success)

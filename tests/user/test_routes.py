from datetime import datetime
from typing import Generator, cast
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from freezegun.api import FrozenDateTimeFactory
from sqlalchemy import Connection, Row, text

from src.auth import SESSION_KEY_NAME
from src.constants import GarageItemRelations
from src.user import service as user_service
from src.user.models import (
    ChangePasswordRequest,
    DeleteGarageItemRequest,
    EditUserFieldRequest,
    ForgotPasswordRequest,
    GarageItem,
    LoginRequest,
    SignUpRequest,
    SignUpResponse,
    SuccessResponse,
    UserDataResponse,
    UserGarageResponse,
)
from src.user.routes import (
    _SESSION_EXPIRE,
    _add_garage_item,
    _change_password_user,
    _delete_garage_item,
    _edit_field_user,
    _forgot_password,
    _get_garage,
    _get_user,
    _login_user,
    _logout_user,
    _signup_user,
)
from tests.factories import (
    encrypt_password,
    make_auth_required,
    store_garage_item,
    store_user,
    store_user_session,
)


class MockResponse:
    def __init__(self) -> None:
        self.cookie_key: str | None = None
        self.cookie_value: str | None = None
        self.cookie_deleted: bool = False
        self.expires: int | None = None

    def set_cookie(self, key: str, value: str, expires: int) -> None:
        self.cookie_key = key
        self.cookie_value = value
        self.expires = expires

    def delete_cookie(self, key: str) -> None:
        self.cookie_deleted = True


@pytest.fixture(scope="function", autouse=True)
def clear(db: Connection) -> Generator:
    yield
    db.execute(text("DELETE FROM user_garage"))
    db.execute(text("DELETE FROM user_sessions"))
    db.execute(text("DELETE FROM users"))
    db.commit()


def _get_first_user_session(db: Connection) -> Row:
    return db.execute(text("SELECT * FROM user_sessions")).first()


def _get_first_user(db: Connection) -> Row:
    return db.execute(text("SELECT * FROM users")).first()


def _get_user_garage(db: Connection, user_id: int) -> list[Row]:
    return list(
        db.execute(text(f"SELECT * FROM user_garage WHERE user_id = {user_id}"))
    )


def _get_user_count(db: Connection) -> int:
    return cast(
        int, db.execute(text("SELECT COUNT(*) as count FROM users")).one_or_none().count
    )


def _get_user_session_count(db: Connection) -> int:
    return cast(
        int,
        db.execute(text("SELECT COUNT(*) as count FROM user_sessions"))
        .one_or_none()
        .count,
    )


@pytest.fixture
def mock_send_mail() -> Mock:
    user_service.send_mail = Mock()
    return user_service.send_mail


@pytest.mark.asyncio
async def test_get_user(db: Connection) -> None:
    # Given
    user_id = store_user(db)
    token = store_user_session(db, user_id=user_id)

    # When
    result = await _get_user(user=make_auth_required(token))

    # Then
    assert result == UserDataResponse(
        user_id=user_id,
        username="user123",
        email="test@gmail.com",
    )


@pytest.mark.asyncio
async def test_get_user_no_token(db: Connection) -> None:
    # Given
    store_user(db)

    # Then
    with pytest.raises(HTTPException):
        await _get_user(user=make_auth_required("bad"))


@pytest.mark.asyncio
async def test_sign_up_success(db: Connection, mock_send_mail: Mock) -> None:
    # Given
    signup_request = SignUpRequest(
        username="user123", email="test@gmail.com", password="123456"
    )
    # When
    result = await _signup_user(signup_request)

    # Then
    user = _get_first_user(db)
    mock_send_mail.assert_called_once_with(
        signup_request.email, "signup", variables={"username": user.username}
    )
    assert user.username == signup_request.username
    assert user.email == signup_request.email
    assert user.password == encrypt_password(signup_request.password)
    assert result == SignUpResponse(success=True, errors=[])


@pytest.mark.asyncio
async def test_sign_up_user_exists_username(
    db: Connection, mock_send_mail: Mock
) -> None:
    # Given
    store_user(db)
    signup_request = SignUpRequest(
        username="user123", email="e@gmail.com", password="123456"
    )
    # When
    result = await _signup_user(signup_request)

    # Then
    mock_send_mail.assert_not_called()
    assert _get_user_count(db) == 1
    assert result == SignUpResponse(
        success=False, errors=["Username already in use. Please use another."]
    )


@pytest.mark.asyncio
async def test_sign_up_user_exists_email(db: Connection, mock_send_mail: Mock) -> None:
    # Given
    store_user(db)
    signup_request = SignUpRequest(
        username="user1234", email="test@gmail.com", password="123456"
    )
    # When
    result = await _signup_user(signup_request)

    # Then
    mock_send_mail.assert_not_called()
    assert _get_user_count(db) == 1
    assert result == SignUpResponse(
        success=False, errors=["Email already in use. Please use another."]
    )


@pytest.mark.asyncio
async def test_sign_up_validations(db: Connection, mock_send_mail: Mock) -> None:
    # Given
    signup_request = SignUpRequest(username="bad", email="bad", password="1234")
    # When
    result = await _signup_user(signup_request)

    # Then
    mock_send_mail.assert_not_called()
    assert _get_user_count(db) == 0
    assert result == SignUpResponse(
        success=False,
        errors=[
            """
      invalid username provided.
      Must be between 3 and 30 characters long,
      and contain normal characters.""",
            """
      invalid password provided.
      Must be between 5 and 50 characters long.""",
            "Invalid email provided.",
        ],
    )


@pytest.mark.asyncio
async def test_login_user(db: Connection, freezer: FrozenDateTimeFactory) -> None:
    # Given
    user_id = store_user(db)
    mock_response = MockResponse()
    login_request = LoginRequest(username="user123", password="pass123")

    # When
    result = await _login_user(login_request, mock_response)
    user_session = _get_first_user_session(db)
    # Then
    assert result == SuccessResponse(success=True)
    assert mock_response.cookie_key == SESSION_KEY_NAME
    assert mock_response.expires == _SESSION_EXPIRE
    assert user_session.user_id == user_id
    assert (
        user_session.expire == int(datetime.timestamp(datetime.now())) + _SESSION_EXPIRE
    )


@pytest.mark.parametrize(
    "username,password",
    (
        ("user-123", "pass123"),
        ("", "pass123"),
        ("user123", "pass-123"),
        ("user123", ""),
        ("", ""),
    ),
)
@pytest.mark.asyncio
async def test_login_user_bad_credentials(
    db: Connection, username: str, password: str
) -> None:
    # Given
    store_user(db)
    mock_response = MockResponse()
    login_request = LoginRequest(username=username, password=password)

    # When
    result = await _login_user(login_request, mock_response)

    # Then
    assert result == SuccessResponse(success=False)
    assert mock_response.cookie_key is None
    assert _get_first_user_session(db) is None


@pytest.mark.asyncio
async def test_login_user_existing_session_not_expired(
    db: Connection, freezer: FrozenDateTimeFactory
) -> None:

    # Given
    user_id = store_user(db)
    token = store_user_session(db, user_id)
    mock_response = MockResponse()
    login_request = LoginRequest(username="user123", password="pass123")

    # When
    result = await _login_user(login_request, mock_response)
    user_session = _get_first_user_session(db)

    # Then
    assert result == SuccessResponse(success=True)
    assert mock_response.cookie_key == SESSION_KEY_NAME
    assert user_session.user_id == user_id
    assert user_session.token == token
    assert _get_user_session_count(db) == 1


@pytest.mark.asyncio
async def test_login_user_existing_session_expired(
    db: Connection, freezer: FrozenDateTimeFactory
) -> None:
    # Given
    user_id = store_user(db)
    token = store_user_session(db, user_id, expire=100)
    mock_response = MockResponse()
    login_request = LoginRequest(username="user123", password="pass123")

    # When
    result = await _login_user(login_request, mock_response)
    user_session = _get_first_user_session(db)

    # Then
    assert result == SuccessResponse(success=True)
    assert mock_response.cookie_key == SESSION_KEY_NAME
    assert user_session.user_id == user_id
    assert user_session.token != token
    assert _get_user_session_count(db) == 1


@pytest.mark.asyncio
async def test_logout_user(db: Connection) -> None:
    # Given
    user_id = store_user(db)
    token = store_user_session(db, user_id)
    mock_response = MockResponse()

    # When
    result = await _logout_user(mock_response, token)

    # Then
    assert result == SuccessResponse(success=True)
    assert mock_response.cookie_deleted
    assert _get_first_user_session(db) is None
    assert _get_user_session_count(db) == 0


@pytest.mark.asyncio
async def test_logout_user_fails(db: Connection) -> None:
    # Given
    mock_response = MockResponse()

    # When
    result = await _logout_user(mock_response, None)

    # Then
    assert result == SuccessResponse(success=False)
    assert not mock_response.cookie_deleted


@pytest.mark.asyncio
async def test_forgot_password_success(db: Connection, mock_send_mail: Mock) -> None:
    # Given
    email = "test@gmail.com"
    username = "test"
    temp_password = "123"
    user_id = store_user(db, username=username, email=email)
    user_service._generate_temp_password = Mock(return_value=temp_password)

    # When
    forgot_password_request = ForgotPasswordRequest(email=email)
    await _forgot_password(forgot_password_request)

    # Then
    user = _get_first_user(db)
    assert user.password == encrypt_password(temp_password)
    mock_send_mail.assert_called_once_with(
        email,
        "temp-password",
        variables={"username": username, "temp_password": temp_password},
    )


@pytest.mark.asyncio
async def test_forgot_password_bad_email(db: Connection, mock_send_mail: Mock) -> None:
    # Given
    password = "123"
    user_id = store_user(db, password=password)
    # When
    forgot_password_request = ForgotPasswordRequest(email="other")
    await _forgot_password(forgot_password_request)

    # Then
    user = _get_first_user(db)
    assert user.password == encrypt_password(password)  # Unchanged
    mock_send_mail.assert_not_called()


@pytest.mark.asyncio
async def test_change_password_user(db: Connection) -> None:
    # Given
    user_id = store_user(db)
    token = store_user_session(db, user_id)
    change_password_request = ChangePasswordRequest(
        username="user123",
        old="pass123",
        new="pass1234",
    )

    # When
    result = await _change_password_user(
        change_password_request,
        user=make_auth_required(token),
    )

    # Then
    assert result == SuccessResponse(success=True)
    assert _get_first_user(db).password == encrypt_password("pass1234")


@pytest.mark.asyncio
async def test_change_password_user_bad_auth(db: Connection) -> None:
    # Given
    user_id = store_user(db)
    token = store_user_session(db, user_id)
    change_password_request = ChangePasswordRequest(
        username="user123",
        old="bad",
        new="pass1234",
    )

    # When
    result = await _change_password_user(
        change_password_request,
        user=make_auth_required(token),
    )

    # Then
    assert result == SuccessResponse(
        success=False,
        errors=["Incorrect current password."],
    )
    assert _get_first_user(db).password == encrypt_password("pass123")


@pytest.mark.asyncio
async def test_change_password_user_invalid(db: Connection) -> None:
    # Given
    user_id = store_user(db)
    token = store_user_session(db, user_id)
    change_password_request = ChangePasswordRequest(
        username="user123",
        old="pass123",
        new="12",
    )

    # When
    result = await _change_password_user(
        change_password_request,
        user=make_auth_required(token),
    )

    # Then
    assert result == SuccessResponse(
        success=False,
        errors=[
            """
      invalid password provided.
      Must be between 5 and 50 characters long.""",
        ],
    )
    assert _get_first_user(db).password == encrypt_password("pass123")


@pytest.mark.asyncio
async def test_edit_field_user(db: Connection) -> None:
    # Given
    user_id = store_user(db)
    token = store_user_session(db, user_id)
    edit_field_request = EditUserFieldRequest(field="username", value="user123456")

    # When
    result = await _edit_field_user(
        edit_field_request,
        user=make_auth_required(token),
    )

    # Then
    assert result == SuccessResponse(success=True)
    assert _get_first_user(db).username == "user123456"


@pytest.mark.asyncio
async def test_edit_field_user_bad_field(db: Connection) -> None:
    # Given
    user_id = store_user(db)
    token = store_user_session(db, user_id)
    edit_field_request = EditUserFieldRequest(field="bad", value="user123456")

    # Then
    with pytest.raises(HTTPException):
        result = await _edit_field_user(
            edit_field_request,
            user=make_auth_required(token),
        )

    assert _get_first_user(db).username == "user123"
    assert _get_first_user(db).email == "test@gmail.com"


@pytest.mark.asyncio
async def test_edit_field_user_username_exists(db: Connection) -> None:
    # Given
    user_id = store_user(db)
    store_user(db, username="othername")
    token = store_user_session(db, user_id)
    edit_field_request = EditUserFieldRequest(field="username", value="othername")

    # When
    result = await _edit_field_user(
        edit_field_request,
        user=make_auth_required(token),
    )

    # Then
    assert result == SuccessResponse(
        success=False,
        errors=["Username already in use. Please use another."],
    )
    assert _get_first_user(db).username == "user123"


@pytest.mark.asyncio
async def test_edit_field_user_email_exists(db: Connection) -> None:
    # Given
    user_id = store_user(db)
    store_user(db, email="other@gmail.com")
    token = store_user_session(db, user_id)
    edit_field_request = EditUserFieldRequest(field="email", value="other@gmail.com")

    # When
    result = await _edit_field_user(
        edit_field_request,
        user=make_auth_required(token),
    )

    # Then
    assert result == SuccessResponse(
        success=False,
        errors=["Email already in use. Please use another."],
    )
    assert _get_first_user(db).email == "test@gmail.com"


@pytest.mark.parametrize("relation", list(GarageItemRelations))
@pytest.mark.asyncio
async def test_add_garage_item(db: Connection, relation: str) -> None:
    # Given
    user_id = store_user(db)
    token = store_user_session(db, user_id)
    garage_item = GarageItem(
        make_name="MakeA",
        name="Name 1",
        year=2022,
        relation=relation,
    )

    # When
    response = await _add_garage_item(
        garage_item,
        user=make_auth_required(token),
    )

    # Then
    results = _get_user_garage(db, user_id)
    assert len(results) == 1
    assert results[0].model_id == 1
    assert results[0].relation == relation
    assert results[0].user_id == user_id
    assert response == SuccessResponse(success=True)


@pytest.mark.asyncio
async def test_add_garage_item_bad_relation(db: Connection) -> None:
    # Given
    user_id = store_user(db)
    token = store_user_session(db, user_id)
    garage_item = GarageItem(
        make_name="MakeA",
        name="Name 1",
        year=2022,
        relation="bad",
    )

    # When
    response = await _add_garage_item(
        garage_item,
        user=make_auth_required(token),
    )

    # Then
    results = _get_user_garage(db, user_id)
    assert len(results) == 0
    assert response == SuccessResponse(success=False)


@pytest.mark.asyncio
async def test_get_garage(db: Connection) -> None:
    # Given
    user_id = store_user(db)
    other_user_id = store_user(db)
    store_garage_item(db, user_id, 1, GarageItemRelations.OWNS.value)
    store_garage_item(db, user_id, 2, GarageItemRelations.OWNS.value)
    store_garage_item(db, user_id, 3, GarageItemRelations.HAS_RIDDEN.value)
    store_garage_item(db, other_user_id, 3, GarageItemRelations.HAS_RIDDEN.value)

    # When
    response = await _get_garage(user_id)

    # Then
    assert response == UserGarageResponse(
        items=[
            GarageItem(
                make_name="MakeA",
                name="Name 1",
                year=2022,
                relation=GarageItemRelations.OWNS.value,
                model_id=1,
            ),
            GarageItem(
                make_name="MakeA",
                name="Name 2",
                year=2021,
                relation=GarageItemRelations.OWNS.value,
                model_id=2,
            ),
            GarageItem(
                make_name="MakeB",
                name="Name 3",
                year=2020,
                relation=GarageItemRelations.HAS_RIDDEN.value,
                model_id=3,
            ),
        ]
    )


@pytest.mark.asyncio
async def test_delete_garage_item(db: Connection) -> None:
    # Given
    user_id = store_user(db)
    token = store_user_session(db, user_id)
    store_garage_item(db, user_id, 1, GarageItemRelations.OWNS.value)
    store_garage_item(db, user_id, 2, GarageItemRelations.OWNS.value)

    delete_garage_item_request = DeleteGarageItemRequest(
        model_id=2,
    )

    # When
    response = await _delete_garage_item(
        delete_garage_item_request,
        user=make_auth_required(token),
    )

    # Then
    results = _get_user_garage(db, user_id)
    assert len(results) == 1
    assert results[0].model_id == 1
    assert response == SuccessResponse(success=True)


@pytest.mark.asyncio
async def test_delete_garage_item_not_exists(db: Connection) -> None:
    # Given
    user_id = store_user(db)
    token = store_user_session(db, user_id)
    store_garage_item(db, user_id, 1, GarageItemRelations.OWNS.value)

    delete_garage_item_request = DeleteGarageItemRequest(
        user_id=user_id,
        model_id=2,
    )

    # When
    response = await _delete_garage_item(
        delete_garage_item_request,
        user=make_auth_required(token),
    )

    # Then
    results = _get_user_garage(db, user_id)
    assert len(results) == 1
    assert results[0].model_id == 1
    assert response == SuccessResponse(success=True)

import pytest
import hashlib
from uuid import uuid4
from datetime import datetime

from sqlalchemy import text

from src.user.routes import (
  get_user,
  signup_user,
  login_user,
  logout_user,
  change_password_user,
  edit_field_user,
  add_garage_item,
  delete_garage_item,
  get_garage,
  _SESSION_KEY_NAME,
  _SESSION_EXPIRE,
)
from src.user.service import GarageItemRelations
from src.user.models import (
  SuccessResponse,
  GarageItem,
  LoginRequest,
  SignUpRequest,
  SignUpResponse,
  UserDataResponse,
  UserGarageResponse,
  DeleteGarageItemRequest,
  ChangePasswordRequest,
  EditUserFieldRequest,
)

_insert_user_query = """
INSERT INTO users
  (username, email, password)
VALUES('{username}', '{email}', '{password}')
"""

_insert_user_session_query = """
INSERT INTO user_sessions
  (token, user_id, expire)
VALUES('{token}', '{user_id}', '{expire}')
"""

_insert_user_garage_query = """
INSERT INTO user_garage
    (user_id, model_id, relation)
VALUES({user_id}, {model_id}, '{relation}')
"""


class MockResponse:
  def __init__(self) -> None:
    self.cookie_key = None
    self.cookie_value = None
    self.cookie_deleted = False
    self.expires = None

  def set_cookie(self, key: str, value: str, expires: int) -> None:
    self.cookie_key = key
    self.cookie_value = value
    self.expires = expires

  def delete_cookie(self, key: str) -> None:
    self.cookie_deleted = True


def encrypt_password(password: str) -> str:
  return hashlib.sha512(password.encode('utf-8')).hexdigest()


@pytest.fixture(scope='function', autouse=True)
def clear(db):
  yield
  db.execute(text('DELETE FROM user_garage'))
  db.execute(text('DELETE FROM user_sessions'))
  db.execute(text('DELETE FROM users'))
  db.commit()


def _store_user(
  db,
  username: str ='user123',
  email: str ='test@gmail.com',
  password: str ='pass123',
) -> int:
  result = db.execute(
    text(
      _insert_user_query.format(
        username=username,
        email=email,
        password=encrypt_password(password),
      )
    )
  )
  db.commit()
  return result.lastrowid


def _store_user_session(
  db,
  user_id: int,
  expire: int | None = None,
) -> int:
  token = uuid4().hex
  expire = expire or int(datetime.timestamp(datetime.now())) + 100
  result = db.execute(
    text(
      _insert_user_session_query.format(
        token=token,
        user_id=user_id,
        expire=expire,
      )
    )
  )
  db.commit()
  return token


def _store_garage_item(
  db,
  user_id: int,
  model_id: int,
  relation: str,
):
  db.execute(
    text(
      _insert_user_garage_query.format(
        user_id=user_id, model_id=model_id, relation=relation,
      )
    )
  )
  db.commit()


def _get_first_user_session(db):
  return db.execute(text('SELECT * FROM user_sessions')).first()


def _get_first_user(db):
  return db.execute(text('SELECT * FROM users')).first()


def _get_user_garage(db, user_id: int):
  return list(db.execute(
    text(f'SELECT * FROM user_garage WHERE user_id = {user_id}')
  ))

def _get_user_count(db):
  return db.execute(
    text('SELECT COUNT(*) as count FROM users')
  ).one_or_none().count


def _get_user_session_count(db):
  return db.execute(
    text('SELECT COUNT(*) as count FROM user_sessions')
  ).one_or_none().count


@pytest.mark.asyncio
async def test_get_user(db):
  # Given
  user_id = _store_user(db)
  token = _store_user_session(db, user_id=user_id)

  # When
  result = await get_user(f'{_SESSION_KEY_NAME}={token}')

  # Then
  assert result == UserDataResponse(
    user_id=user_id,
    username='user123',
    email='test@gmail.com',
  )


@pytest.mark.asyncio
async def test_get_user_no_cookie(db):
  # Given
  user_id = _store_user(db)
  token = _store_user_session(db, user_id=user_id)

  # When
  result = await get_user(None)

  # Then
  assert result is None


@pytest.mark.asyncio
async def test_sign_up_success(db):
  # Given
  signup_request = SignUpRequest(
    username='user123', email='test@gmail.com', password='123456'
  )
  # When
  result = await signup_user(signup_request)

  # Then
  user = _get_first_user(db)
  assert user.username == signup_request.username
  assert user.email == signup_request.email
  assert user.password == encrypt_password(signup_request.password)
  assert result == SignUpResponse(success=True, errors=[])


@pytest.mark.asyncio
async def test_sign_up_user_exists_username(db):
  # Given
  _store_user(db)
  signup_request = SignUpRequest(
    username='user123', email='e@gmail.com', password='123456'
  )
  # When
  result = await signup_user(signup_request)

  # Then
  assert _get_user_count(db) == 1
  assert result == SignUpResponse(
    success=False,
    errors=['Username already in use. Please use another.']
  )

@pytest.mark.asyncio
async def test_sign_up_user_exists_email(db):
  # Given
  _store_user(db)
  signup_request = SignUpRequest(
    username='user1234', email='test@gmail.com', password='123456'
  )
  # When
  result = await signup_user(signup_request)

  # Then
  assert _get_user_count(db) == 1
  assert result == SignUpResponse(
    success=False,
    errors=['Email already in use. Please use another.']
  )

@pytest.mark.asyncio
async def test_sign_up_validations(db):
  # Given
  signup_request = SignUpRequest(
    username='bad', email='bad', password='1234'
  )
  # When
  result = await signup_user(signup_request)

  # Then
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
      'Invalid email provided.',
    ]
  )

@pytest.mark.asyncio
async def test_login_user(db, freezer):
  # Given
  user_id = _store_user(db)
  mock_response = MockResponse()
  login_request = LoginRequest(username='user123', password='pass123')

  # When
  result = await login_user(login_request, mock_response)
  user_session = _get_first_user_session(db)
  # Then
  assert result == SuccessResponse(success=True)
  assert mock_response.cookie_key == _SESSION_KEY_NAME
  assert mock_response.expires == _SESSION_EXPIRE
  assert user_session.user_id == user_id
  assert user_session.expire == int(
    datetime.timestamp(datetime.now())
  ) + _SESSION_EXPIRE


@pytest.mark.parametrize(
  "username,password",
  (
    ("user-123", "pass123"),
    ("", "pass123"),
    ("user123", "pass-123"),
    ("user123", ""),
    ("", ""),
  )
)
@pytest.mark.asyncio
async def test_login_user_bad_credentials(
  db, username: str, password: str
):
  # Given
  user_id = _store_user(db)
  mock_response = MockResponse()
  login_request = LoginRequest(username=username, password=password)

  # When
  result = await login_user(login_request, mock_response)

  # Then
  assert result == SuccessResponse(success=False)
  assert mock_response.cookie_key is None
  assert _get_first_user_session(db) is None


@pytest.mark.asyncio
async def test_login_user_existing_session_not_expired(db, freezer):
  # Given
  user_id = _store_user(db)
  token = _store_user_session(db, user_id)
  mock_response = MockResponse()
  login_request = LoginRequest(username='user123', password='pass123')

  # When
  result = await login_user(login_request, mock_response)
  user_session = _get_first_user_session(db)

  # Then
  assert result == SuccessResponse(success=True)
  assert mock_response.cookie_key == _SESSION_KEY_NAME
  assert user_session.user_id == user_id
  assert user_session.token == token
  assert _get_user_session_count(db) == 1


@pytest.mark.asyncio
async def test_login_user_existing_session_expired(db, freezer):
  # Given
  user_id = _store_user(db)
  token = _store_user_session(db, user_id, expire=100)
  mock_response = MockResponse()
  login_request = LoginRequest(username='user123', password='pass123')

  # When
  result = await login_user(login_request, mock_response)
  user_session = _get_first_user_session(db)

  # Then
  assert result == SuccessResponse(success=True)
  assert mock_response.cookie_key == _SESSION_KEY_NAME
  assert user_session.user_id == user_id
  assert user_session.token != token
  assert _get_user_session_count(db) == 1


@pytest.mark.asyncio
async def test_logout_user(db):
  # Given
  user_id = _store_user(db)
  token = _store_user_session(db, user_id)
  mock_response = MockResponse()

  # When
  result = await logout_user(
    mock_response, f'{_SESSION_KEY_NAME}={token}'
  )

  # Then
  assert result == SuccessResponse(success=True)
  assert mock_response.cookie_deleted
  assert _get_first_user_session(db) is None
  assert _get_user_session_count(db) == 0


@pytest.mark.asyncio
async def test_logout_user_fails(db):
  # Given
  mock_response = MockResponse()

  # When
  result = await logout_user(
    mock_response, f'{_SESSION_KEY_NAME}=123'
  )

  # Then
  assert result == SuccessResponse(success=False)
  assert not mock_response.cookie_deleted


@pytest.mark.asyncio
async def test_change_password_user(db):
  # Given
  user_id = _store_user(db)
  token = _store_user_session(db, user_id)
  change_password_request = ChangePasswordRequest(
    username='user123', old='pass123', new='pass1234',
  )

  # When
  result = await change_password_user(
    change_password_request, cookie=f'{_SESSION_KEY_NAME}={token}',
  )

  # Then
  assert result == SuccessResponse(success=True)
  assert _get_first_user(db).password == encrypt_password('pass1234')


@pytest.mark.asyncio
async def test_change_password_user_bad_auth(db):
  # Given
  user_id = _store_user(db)
  token = _store_user_session(db, user_id)
  change_password_request = ChangePasswordRequest(
    username='user123', old='bad', new='pass1234',
  )

  # When
  result = await change_password_user(
    change_password_request, cookie=f'{_SESSION_KEY_NAME}={token}',
  )

  # Then
  assert result == SuccessResponse(
    success=False, errors=['Incorrect current password.'],
  )
  assert _get_first_user(db).password == encrypt_password('pass123')


@pytest.mark.asyncio
async def test_change_password_user_invalid(db):
  # Given
  user_id = _store_user(db)
  token = _store_user_session(db, user_id)
  change_password_request = ChangePasswordRequest(
    username='user123', old='pass123', new='12',
  )

  # When
  result = await change_password_user(
    change_password_request, cookie=f'{_SESSION_KEY_NAME}={token}',
  )

  # Then
  assert result == SuccessResponse(
    success=False, errors=[
      """
      invalid password provided.
      Must be between 5 and 50 characters long.""",
    ]
  )
  assert _get_first_user(db).password == encrypt_password('pass123')


@pytest.mark.asyncio
async def test_edit_field_user(db):
  # Given
  user_id = _store_user(db)
  token = _store_user_session(db, user_id)
  edit_field_request = EditUserFieldRequest(
    field='username', value='user123456'
  )

  # When
  result = await edit_field_user(
    edit_field_request, cookie=f'{_SESSION_KEY_NAME}={token}',
  )

  # Then
  assert result == SuccessResponse(success=True)
  assert _get_first_user(db).username == 'user123456'


@pytest.mark.asyncio
async def test_edit_field_user_bad_field(db):
  # Given
  user_id = _store_user(db)
  token = _store_user_session(db, user_id)
  edit_field_request = EditUserFieldRequest(
    field='bad', value='user123456'
  )

  # When
  result = await edit_field_user(
    edit_field_request, cookie=f'{_SESSION_KEY_NAME}={token}',
  )

  # Then
  assert result == SuccessResponse(success=False, errors=['Field unknown'])
  assert _get_first_user(db).username == 'user123'
  assert _get_first_user(db).email == 'test@gmail.com'


@pytest.mark.asyncio
async def test_edit_field_user_username_exists(db):
  # Given
  user_id = _store_user(db)
  _store_user(db, username='othername')
  token = _store_user_session(db, user_id)
  edit_field_request = EditUserFieldRequest(
    field='username', value='othername'
  )

  # When
  result = await edit_field_user(
    edit_field_request, cookie=f'{_SESSION_KEY_NAME}={token}',
  )

  # Then
  assert result == SuccessResponse(
    success=False,
    errors=['Username already in use. Please use another.'],
  )
  assert _get_first_user(db).username == 'user123'


@pytest.mark.asyncio
async def test_edit_field_user_email_exists(db):
  # Given
  user_id = _store_user(db)
  _store_user(db, email='other@gmail.com')
  token = _store_user_session(db, user_id)
  edit_field_request = EditUserFieldRequest(
    field='email', value='other@gmail.com'
  )

  # When
  result = await edit_field_user(
    edit_field_request, cookie=f'{_SESSION_KEY_NAME}={token}',
  )

  # Then
  assert result == SuccessResponse(
    success=False,
    errors=['Email already in use. Please use another.'],
  )
  assert _get_first_user(db).email == 'test@gmail.com'


@pytest.mark.parametrize(
  'relation',
  list(GarageItemRelations)
)
@pytest.mark.asyncio
async def test_add_garage_item(db, relation: str) -> None:
  # Given
  user_id = _store_user(db)
  token = _store_user_session(db, user_id)
  garage_item = GarageItem(
    make_name='MakeA',
    name='Name 1',
    year=2022,
    relation=relation,
  )

  # When
  response = await add_garage_item(
    garage_item, cookie=f'{_SESSION_KEY_NAME}={token}',
  )

  # Then
  results = _get_user_garage(db, user_id)
  assert len(results) == 1
  assert results[0].model_id == 1
  assert results[0].relation == relation
  assert results[0].user_id == user_id
  assert response == SuccessResponse(success=True)


@pytest.mark.asyncio
async def test_add_garage_item_bad_relation(db) -> None:
  # Given
  user_id = _store_user(db)
  token = _store_user_session(db, user_id)
  garage_item = GarageItem(
    make_name='MakeA',
    name='Name 1',
    year=2022,
    relation='bad',
  )

  # When
  response = await add_garage_item(
    garage_item, cookie=f'{_SESSION_KEY_NAME}={token}',
  )

  # Then
  results = _get_user_garage(db, user_id)
  assert len(results) == 0
  assert response == SuccessResponse(success=False)


@pytest.mark.asyncio
async def test_get_garage(db) -> None:
  # Given
  user_id = _store_user(db)
  other_user_id = _store_user(db)
  _store_garage_item(db, user_id, 1, GarageItemRelations.OWNS.value)
  _store_garage_item(db, user_id, 2, GarageItemRelations.OWNS.value)
  _store_garage_item(db, user_id, 3, GarageItemRelations.HAS_RIDDEN.value)
  _store_garage_item(db, other_user_id, 3, GarageItemRelations.HAS_RIDDEN.value)

  # When
  response = await get_garage(user_id)

  # Then
  assert response == UserGarageResponse(
    items=[
      GarageItem(
        make_name='MakeA',
        name='Name 1',
        year=2022,
        relation=GarageItemRelations.OWNS.value,
        model_id=1,
      ),
      GarageItem(
        make_name='MakeA',
        name='Name 2',
        year=2021,
        relation=GarageItemRelations.OWNS.value,
        model_id=2,
      ),
      GarageItem(
        make_name='MakeB',
        name='Name 3',
        year=2020,
        relation=GarageItemRelations.HAS_RIDDEN.value,
        model_id=3,
      ),
    ]
  )


@pytest.mark.asyncio
async def test_delete_garage_item(db) -> None:
  # Given
  user_id = _store_user(db)
  token = _store_user_session(db, user_id)
  _store_garage_item(db, user_id, 1, GarageItemRelations.OWNS.value)
  _store_garage_item(db, user_id, 2, GarageItemRelations.OWNS.value)

  delete_garage_item_request = DeleteGarageItemRequest(
    model_id=2,
  )

  # When
  response = await delete_garage_item(
    delete_garage_item_request, cookie=f'{_SESSION_KEY_NAME}={token}',
  )

  # Then
  results = _get_user_garage(db, user_id)
  assert len(results) == 1
  assert results[0].model_id == 1
  assert response == SuccessResponse(success=True)


@pytest.mark.asyncio
async def test_delete_garage_item_not_exists(db) -> None:
  # Given
  user_id = _store_user(db)
  token = _store_user_session(db, user_id)
  _store_garage_item(db, user_id, 1, GarageItemRelations.OWNS.value)

  delete_garage_item_request = DeleteGarageItemRequest(
    user_id=user_id,
    model_id=2,
  )

  # When
  response = await delete_garage_item(
    delete_garage_item_request, cookie=f'{_SESSION_KEY_NAME}={token}',
  )

  # Then
  results = _get_user_garage(db, user_id)
  assert len(results) == 1
  assert results[0].model_id == 1
  assert response == SuccessResponse(success=True)

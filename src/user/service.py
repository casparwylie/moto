import hashlib
from uuid import uuid4
from datetime import datetime

from src.database import engine as db
from src.racing.service import get_racer
from src.user.queries import (
  build_check_user_exists_query,
  build_signup_query,
  build_user_auth_query,
  build_make_user_session_query,
  build_get_user_session_query,
  build_get_user_by_token_query,
  build_delete_session_query,
  build_get_user_garage_query,
  build_get_model_id_query,
  build_add_user_garage_item_query,
)

#############
### UTILS ###
#############

def encrypt_password(password):
  return hashlib.sha512(password.encode('utf-8')).hexdigest()

def generate_user_session_token():
  return uuid4().hex


################
### SESSIONS ###
################


def delete_session(token: str):
  with db.connect() as conn:
    conn.execute(build_delete_session_query(token))
    conn.commit()


def get_user_by_token(token: str) -> str | None:
  with db.connect() as conn:
    user = conn.execute(
        build_get_user_by_token_query(token)
    ).one_or_none()
    if user:
      return user


def expired_session(expires_timestamp) -> bool:
  return bool(
    datetime.fromtimestamp(expires_timestamp) < datetime.now()
  )

def get_user_token(user_id: str, expires: int) -> str | None:
  with db.connect() as conn:
    session = conn.execute(
        build_get_user_session_query(user_id)
    ).one_or_none()
    if session:
      if expired_session(session.expire):
        delete_session(session.token)
      else:
        return session.token
    new_token = generate_user_session_token()
    timestamp_now = int(datetime.timestamp(datetime.now()))
    session = conn.execute(
      build_make_user_session_query(
        new_token,
        user_id,
        timestamp_now + expires,
      )
    )
    conn.commit()
  return new_token


def login(username: str, password: str, expires: int) -> str | None:
  encrypted_pass = encrypt_password(password)
  with db.connect() as conn:
    user = conn.execute(
      build_user_auth_query(username, encrypted_pass)
    ).one_or_none()
    if user:
      return get_user_token(user.id, expires)


##############
### SIGNUP ###
##############

def check_user_exists(username: str, email: str) -> str | None:
  with db.connect() as conn:
    result = conn.execute(
      build_check_user_exists_query(username, email)
    ).first()
  if result and result.email == email:
    return 'email'
  elif result and result.username == username:
    return 'username'


def signup(username: str, password: str, email: str) -> None:
  encrypted_pass = encrypt_password(password)
  with db.connect() as conn:
    user = conn.execute(
      build_signup_query(username, encrypted_pass, email)
    )
    user_id = user.lastrowid
    conn.commit()


###############
### PROFILE ###
###############

_GARAGE_ITEM_RELATIONS = (
  'ridden',
  'owns',
)


def add_user_garage_item(
  user_id: int, make: str, model: str, year: int, relation: str
) -> bool:
  if relation not in _GARAGE_ITEM_RELATIONS:
    return False
  with db.connect() as conn:
    model = conn.execute(build_get_model_id_query(make, model, year)).first()
    conn.execute(build_add_user_garage_item_query(user_id, model.id, relation))
    conn.commit()
    return True


def get_user_garage(user_id: int):
  with db.connect() as conn:
    return conn.execute(build_get_user_garage_query(user_id)).all()

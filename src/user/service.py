import hashlib
from datetime import datetime
from enum import Enum
from typing import cast
from uuid import uuid4

from sqlalchemy import Row

from src.database import engine as db
from src.racing.service import get_racer
from src.user.queries import (
    build_add_user_garage_item_query,
    build_change_password_query,
    build_check_user_exists_query,
    build_delete_session_query,
    build_delete_user_garage_item_query,
    build_get_model_id_query,
    build_get_user_by_token_query,
    build_get_user_garage_query,
    build_get_user_session_query,
    build_make_user_session_query,
    build_signup_query,
    build_update_user_field_query,
    build_user_auth_query,
)

#############
### UTILS ###
#############


def encrypt_password(password: str) -> str:
    return hashlib.sha512(password.encode("utf-8")).hexdigest()


def generate_user_session_token() -> str:
    return uuid4().hex


################
### SESSIONS ###
################


def delete_session(token: str) -> None:
    with db.connect() as conn:
        conn.execute(build_delete_session_query(token))
        conn.commit()


def get_user_by_token(token: str) -> Row | None:
    with db.connect() as conn:
        user = conn.execute(build_get_user_by_token_query(token)).one_or_none()
        if user:
            return user


def expired_session(expires_timestamp) -> bool:
    return bool(datetime.fromtimestamp(expires_timestamp) < datetime.now())


def get_user_token(user_id: int, expires: int) -> str | None:
    with db.connect() as conn:
        session = conn.execute(build_get_user_session_query(user_id)).one_or_none()
        if session:
            if expired_session(session.expire):
                delete_session(session.token)
            else:
                return cast(str, session.token)
        new_token = generate_user_session_token()
        timestamp_now = int(datetime.timestamp(datetime.now()))
        conn.execute(
            build_make_user_session_query(
                new_token,
                user_id,
                timestamp_now + expires,
            )
        )
        conn.commit()
    return new_token


def _authenticate(username: str, password: str) -> None | int:
    encrypted_pass = encrypt_password(password)
    with db.connect() as conn:
        user = conn.execute(
            build_user_auth_query(username, encrypted_pass)
        ).one_or_none()
        if user:
            return cast(int, user.id)


def login(username: str, password: str, expires: int) -> str | None:
    with db.connect() as conn:
        if user_id := _authenticate(username, password):
            return get_user_token(user_id, expires)


##############
### SIGNUP ###
##############


def check_user_exists(username: str, email: str) -> str | None:
    with db.connect() as conn:
        result = conn.execute(build_check_user_exists_query(username, email)).first()
    if result and result.email == email:
        return "email"
    elif result and result.username == username:
        return "username"


def signup(username: str, password: str, email: str) -> None:
    encrypted_pass = encrypt_password(password)
    with db.connect() as conn:
        user = conn.execute(build_signup_query(username, encrypted_pass, email))
        user.lastrowid
        conn.commit()


###############
### PROFILE ###
###############


class GarageItemRelations(str, Enum):
    HAS_OWNED = "HAS_OWNED"
    OWNS = "OWNS"
    HAS_RIDDEN = "HAS_RIDDEN"
    SAT_ON = "SAT_ON"


_USER_EDITABLE_FIELDS = ("username", "email")


def change_password(username: str, old: str, new: str) -> bool:
    if user_id := _authenticate(username, old):
        with db.connect() as conn:
            conn.execute(build_change_password_query(user_id, encrypt_password(new)))
            conn.commit()
        return True
    else:
        return False


def edit_user_field(user_id, field: str, value: str) -> bool:
    if field not in _USER_EDITABLE_FIELDS:
        return False
    with db.connect() as conn:
        conn.execute(build_update_user_field_query(user_id, field, value))
        conn.commit()
    return True


def add_user_garage_item(
    user_id: int, make: str, model: str, year: int, relation: str
) -> bool:
    if relation not in list(GarageItemRelations):
        return False
    with db.connect() as conn:
        result = conn.execute(build_get_model_id_query(make, model, year)).first()
        if result:
            conn.execute(build_add_user_garage_item_query(user_id, result.id, relation))
            conn.commit()
            return True
        return False


def delete_user_garage_item(user_id: int, model_id: int) -> bool:
    with db.connect() as conn:
        conn.execute(build_delete_user_garage_item_query(user_id, model_id))
        conn.commit()
        return True


def get_user_garage(user_id: int) -> list[Row]:
    with db.connect() as conn:
        return list(conn.execute(build_get_user_garage_query(user_id)).all())

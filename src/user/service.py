import hashlib
from datetime import datetime
from typing import cast
from uuid import uuid4

from sqlalchemy import Row

from src.constants import GarageItemRelations
from src.database import engine as db
from src.mail import send_mail
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


def _encrypt_password(password: str) -> str:
    return hashlib.sha512(password.encode("utf-8")).hexdigest()


def _generate_user_session_token() -> str:
    return uuid4().hex


def _generate_temp_password() -> str:
    return uuid4().hex[:7]


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


def expired_session(expires_timestamp: int) -> bool:
    return bool(datetime.fromtimestamp(expires_timestamp) < datetime.now())


def get_user_token(user_id: int, expires: int) -> str | None:
    with db.connect() as conn:
        session = conn.execute(build_get_user_session_query(user_id)).one_or_none()
        if session:
            if expired_session(session.expire):
                delete_session(session.token)
            else:
                return cast(str, session.token)
        new_token = _generate_user_session_token()
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


def authenticate(username: str, password: str) -> None | int:
    encrypted_pass = _encrypt_password(password)
    with db.connect() as conn:
        user = conn.execute(
            build_user_auth_query(username, encrypted_pass)
        ).one_or_none()
        if user:
            return cast(int, user.id)


def login(username: str, password: str, expires: int) -> str | None:
    with db.connect() as conn:
        if user_id := authenticate(username, password):
            return get_user_token(user_id, expires)


##############
### SIGNUP ###
##############


def check_user_exists(username: str, email: str) -> Row | None:
    with db.connect() as conn:
        result = conn.execute(
            build_check_user_exists_query(username, email)
        ).one_or_none()
        return result


def signup(username: str, password: str, email: str) -> None:
    encrypted_pass = _encrypt_password(password)
    with db.connect() as conn:
        user = conn.execute(build_signup_query(username, encrypted_pass, email))
        user.lastrowid
        conn.commit()
    send_mail(email, "signup", variables={"username": username})


###############
### PROFILE ###
###############


_USER_EDITABLE_FIELDS = ("username", "email")


def set_temp_password(user: Row) -> None:
    temp_password = _generate_temp_password()
    change_password(user.id, temp_password)
    send_mail(
        user.email,
        "temp-password",
        variables={"username": user.username, "temp_password": temp_password},
    )


def change_password(user_id: int, new: str) -> None:
    with db.connect() as conn:
        conn.execute(build_change_password_query(user_id, _encrypt_password(new)))
        conn.commit()


def edit_user_field(user_id: int, field: str, value: str) -> bool:
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
        print("relation", relation)
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

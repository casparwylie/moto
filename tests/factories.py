import hashlib
from datetime import datetime
from typing import cast
from uuid import uuid4

from sqlalchemy import Connection, Row, text

from src.auth import SESSION_KEY_NAME, auth_optional, auth_required

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


def encrypt_password(password: str) -> str:
    return hashlib.sha512(password.encode("utf-8")).hexdigest()


def make_auth_required(token: str) -> Row:
    return auth_required(f"{SESSION_KEY_NAME}={token}")


def make_auth_optional(token: str) -> Row:
    return auth_optional(f"{SESSION_KEY_NAME}={token}")


def store_user(
    db: Connection,
    username: str = "user123",
    email: str = "test@gmail.com",
    password: str = "pass123",
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
    return cast(int, result.lastrowid)


def store_user_session(
    db: Connection,
    user_id: int,
    expire: int | None = None,
) -> str:
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

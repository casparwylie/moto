import hashlib
from datetime import datetime
from typing import cast
from uuid import uuid4

from sqlalchemy import Connection, Row, text

from src.auth import auth_optional, auth_required
from src.racing.service import make_unique_race_id

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
    return auth_required(token)


def make_auth_optional(token: str) -> Row:
    return auth_optional(token)


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


def store_race(
    db: Connection, model_ids: list[int], user_id: None | int = None
) -> tuple[int, str]:
    race_unique_id = make_unique_race_id(model_ids)
    db.execute(text(f"INSERT IGNORE race_unique (id) VALUES('{race_unique_id}')"))
    if user_id:
        result = db.execute(
            text(
                f"INSERT INTO race_history (user_id, race_unique_id) VALUES({user_id}, '{race_unique_id}')"
            )
        )
    else:
        result = db.execute(
            text(
                f"INSERT INTO race_history (race_unique_id) VALUES('{race_unique_id}')"
            )
        )
    race_id = cast(int, result.lastrowid)
    for model_id in model_ids:
        db.execute(text(f"INSERT INTO race_racers VALUES({race_id}, {model_id})"))
    db.commit()
    return race_id, race_unique_id

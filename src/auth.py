from fastapi import Cookie, HTTPException, status
from sqlalchemy import Row

from src.user.service import get_user_by_token

SESSION_KEY_NAME = "session_token"


def _auth(session_token: str | None) -> None | Row:
    if session_token and (user := get_user_by_token(session_token)):
        return user


def get_token(session_token: None | str = Cookie(None)) -> None | str:
    return session_token


def auth_required(session_token: None | str = Cookie(None)) -> Row:
    if user := _auth(session_token):
        return user
    raise HTTPException(status.HTTP_403_FORBIDDEN)


def auth_optional(session_token: None | str = Cookie(None)) -> None | Row:
    return _auth(session_token)

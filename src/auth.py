from fastapi import Header, HTTPException, status
from sqlalchemy import Row

from src.user.service import get_user_by_token

SESSION_KEY_NAME = "session_token"


def _get_token_from_cookie(cookie: str | None) -> str | None:
    if cookie:
        parts = cookie.split("=")
        return parts[1] if parts[0] == SESSION_KEY_NAME else None


def _auth(cookie: str | None) -> None | Row:
    if token := _get_token_from_cookie(cookie):
        if user := get_user_by_token(token):
            return user


def get_token(cookie: str = Header(None)) -> None | str:
    return _get_token_from_cookie(cookie)


def auth_required(cookie: str = Header(None)) -> Row:
    if user := _auth(cookie):
        return user
    raise HTTPException(status.HTTP_403_FORBIDDEN)


def auth_optional(cookie: str = Header(None)) -> None | Row:
    return _auth(cookie)

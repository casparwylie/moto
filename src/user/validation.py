import re

from email_validator import EmailNotValidError
from email_validator import validate_email as _validate_email


def invalid_email(email: str) -> bool | str:
    try:
        _validate_email(email, check_deliverability=True)
        return False
    except EmailNotValidError:
        return "Invalid email provided."


def invalid_username(username: str) -> bool | str:
    if (30 > len(username) > 3) and (re.match(r"^[\w][\w_.-]+$", username)):
        return False
    else:
        return """
      invalid username provided.
      Must be between 3 and 30 characters long,
      and contain normal characters."""


def invalid_password(password: str) -> bool | str:
    if 50 > len(password) > 5:
        return False
    else:
        return """
      invalid password provided.
      Must be between 5 and 50 characters long."""

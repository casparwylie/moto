from datetime import datetime

from sqlalchemy import text

from src.database import engine as db


def _expire_user_sessions() -> None:
    timestamp_now = int(datetime.timestamp(datetime.now()))
    with db.connect() as conn:
        conn.execute(text(f"DELETE FROM user_sessions WHERE expire < {timestamp_now}"))
        conn.commit()


SEQUENCE = {"Expire user sessions": _expire_user_sessions}


def run_startup_sequence() -> None:
    for name, task in SEQUENCE.items():
        print(f"[STARTUP] Running {name}")
        task()

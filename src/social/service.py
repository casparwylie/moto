from sqlalchemy import Row

from src.database import engine as db
from src.social.queries import build_add_comment_query, build_get_comments_query


def add_race_comment(text: str, race_unique_id: str, user_id: int) -> bool:
    with db.connect() as conn:
        conn.execute(build_add_comment_query(text, race_unique_id, user_id))
        conn.commit()
        return True


def get_race_comments(race_unique_id: str) -> list[Row]:
    with db.connect() as conn:
        return list(conn.execute(build_get_comments_query(race_unique_id)).all())

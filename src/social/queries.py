from datetime import datetime

from sqlalchemy import Insert, Select, insert, select

from src.database import race_comments_table, users_table


def build_add_comment_query(text: str, race_unique_id: str, user_id: int) -> Insert:

    return insert(race_comments_table).values(
        text=text,
        race_unique_id=race_unique_id,
        user_id=user_id,
        created_at=int(datetime.timestamp(datetime.now())),
    )


def build_get_comments_query(race_unique_id: str) -> Select:
    return (
        select(race_comments_table, users_table.c.username)
        .where(
            race_comments_table.c.race_unique_id == race_unique_id,
        )
        .join(
            users_table,
            users_table.c.id == race_comments_table.c.user_id,
        )
        .order_by(race_comments_table.c.created_at.asc())
    )

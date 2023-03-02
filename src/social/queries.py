from datetime import datetime

from sqlalchemy import Delete, Insert, Select, Text, delete, insert, select, text

from src.database import race_comments_table, users_table


def build_add_comment_query(text: str, race_unique_id: str, user_id: int) -> Insert:

    return insert(race_comments_table).values(
        text=text,
        race_unique_id=race_unique_id,
        user_id=user_id,
        created_at=int(datetime.timestamp(datetime.now())),
    )


def build_delete_comment_query(comment_id: int, user_id: int) -> Delete:
    return delete(race_comments_table).where(
        race_comments_table.c.id == comment_id,
        race_comments_table.c.user_id == user_id,
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


def build_user_garage_race_relation_query(user_id: int, race_unique_id: str) -> Text:
    return text(
        f"""
    SELECT * FROM user_garage
    JOIN racer_models ON racer_models.id = user_garage.model_id
    JOIN users ON user_garage.user_id = users.id
    WHERE user_garage.user_id = {user_id}
    AND user_garage.model_id IN (
      SELECT model_id from race_racers WHERE race_id IN (
        SELECT id FROM race_history
        WHERE race_unique_id = '{race_unique_id}'
      )
    )
  """
    )

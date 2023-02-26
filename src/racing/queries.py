from sqlalchemy import (
    Insert,
    Select,
    Text,
    distinct,
    func,
    insert,
    literal_column,
    select,
    text,
)

from src.database import (
    race_history_table,
    race_racers_table,
    race_votes_table,
    racer_makes_table,
    racer_models_table,
)


def build_search_racer_query(make: str, model: str, year: str) -> Select:
    return (
        select(
            racer_models_table.columns,
            racer_makes_table.c.name.label("make_name"),
        )
        .having(
            racer_models_table.c.name.contains(model),
            racer_models_table.c.year.contains(year),
            literal_column("make_name").contains(make),
        )
        .join(racer_makes_table, racer_makes_table.c.id == racer_models_table.c.make)
    )


def build_get_race_racers_query(race_id: int) -> Select:
    return (
        select(
            racer_models_table,
            racer_makes_table.c.name.label("make_name"),
        )
        .where(race_racers_table.c.race_id == race_id)
        .join(
            race_racers_table, race_racers_table.c.model_id == racer_models_table.c.id
        )
        .join(
            racer_makes_table,
            racer_makes_table.c.id == racer_models_table.c.make,
        )
    )


def build_get_race_query(race_id: int) -> Select:
    return select(race_history_table).where(race_history_table.c.id == race_id)


def build_get_racer_by_make_model_query(
    make: str, model: str, year: str | None
) -> Select:
    filters = [
        racer_models_table.c.name == model,
        literal_column("make_name") == make,
    ]
    if year:
        filters.append(racer_models_table.c.year == year)
    return (
        select(
            racer_models_table.columns,
            racer_makes_table.c.name.label("make_name"),
        )
        .having(*filters)
        .join(racer_makes_table, racer_makes_table.c.id == racer_models_table.c.make)
    )


def build_insert_race_query(race_unique_id: str, user_id: None | int = None) -> Insert:
    return insert(race_history_table).values(
        race_unique_id=race_unique_id, user_id=user_id
    )


def build_insert_race_racers_query(race_id: int, model_ids: list[int]) -> Insert:
    return insert(race_racers_table).values(
        [dict(race_id=race_id, model_id=model_id) for model_id in model_ids]
    )


def build_popular_pairs_query(limit: int) -> Text:
    return text(
        f"""
    SELECT
      p1.id AS id_1,
      p2.id AS id_2,
      occurence
    FROM (
      SELECT
          t1.model_id AS t1_id,
          t2.model_id AS t2_id,
          COUNT(*) AS occurence
      FROM race_racers t1
      JOIN race_racers t2
      ON t1.race_id = t2.race_id
      AND t1.model_id < t2.model_id
      GROUP BY
          t1_id,
          t2_id
    ) AS pairs
    JOIN racer_models p1
      ON p1.id = pairs.t1_id
    JOIN racer_models p2
      ON p2.id = pairs.t2_id
    WHERE occurence > 1
    ORDER BY occurence DESC LIMIT {limit}
    """
    )


def build_most_recent_races_query(user_id: int | None = None) -> Select:
    filters = (race_history_table.c.user_id == user_id,) if user_id else ()
    return (
        select(race_history_table)
        .where(*filters)
        .order_by(race_history_table.c.created_at.desc())
    )


def build_check_race_by_racers_query(race_unique_id: str) -> Select:
    return select(race_history_table).where(
        race_history_table.c.race_unique_id == race_unique_id
    )


def build_get_race_upvotes_query(race_unique_id: str) -> Text:
    return text(
        f"""
      SELECT COUNT(*) as count FROM race_votes WHERE race_unique_id = '{race_unique_id}'
      AND vote = 1
    """
    )


def build_get_race_downvotes_query(race_unique_id: str) -> Text:
    return text(
        f"""
      SELECT COUNT(*) as count FROM race_votes WHERE race_unique_id = '{race_unique_id}'
      AND vote = 0
    """
    )


def build_check_user_vote_query(race_unique_id: str, user_id: int) -> Select:
    return select(race_votes_table).where(
        race_votes_table.c.race_unique_id == race_unique_id,
        race_votes_table.c.user_id == user_id,
    )


def build_vote_race_query(race_unique_id: str, user_id: int, vote: int) -> Insert:
    return insert(race_votes_table).values(
        race_unique_id=race_unique_id,
        user_id=user_id,
        vote=vote,
    )


def build_insert_race_unique_query(unique_id: str) -> Text:
    return text(f"INSERT IGNORE race_unique VALUES('{unique_id}')")

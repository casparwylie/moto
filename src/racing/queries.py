from sqlalchemy import (
    Insert,
    Select,
    Text,
    distinct,
    insert,
    literal_column,
    select,
    text,
)

from src.database import (
    race_history_table,
    race_racers_table,
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


def build_insert_race_query() -> Insert:
    return insert(race_history_table)


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


def build_most_recent_races_query() -> Select:
    return select(race_history_table.columns).order_by(
        race_history_table.c.created_at.desc()
    )


def build_check_race_by_racers_query(model_ids: list[int]) -> Text:
    return text(
        f"""
      SELECT race_id
      FROM race_racers WHERE race_id IN (
        SELECT race_id
        FROM race_racers
        WHERE model_id IN ({','.join(map(str, model_ids))})
        GROUP BY race_id
        HAVING COUNT(DISTINCT model_id) = {len(model_ids)}
      )
      GROUP BY race_id HAVING COUNT(*) = {len(model_ids)}
    """
    )

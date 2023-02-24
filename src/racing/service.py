from sqlalchemy import Row
from typing import Generator
from src.database import engine as db
from src.racing.queries import (
    build_get_race_query,
    build_get_race_racers_query,
    build_get_racer_by_make_model_query,
    build_insert_race_query,
    build_insert_race_racers_query,
    build_search_racer_query,
    build_popular_pairs_query,
    build_most_recent_races_query,
    build_check_race_by_racers_query,
)


_MAX_SEARCH_RESULT = 20
_MAX_RECENT_RACES = 30
_MAX_POPULAR_PAIRS = 10


def get_racer(make: str, model: str, year: str) -> Row | None:
    if make and model:
        with db.connect() as conn:
            return conn.execute(
                build_get_racer_by_make_model_query(make, model, year)
            ).first()


def get_race(race_id: int) -> tuple[None | Row, list[Row]]:
    with db.connect() as conn:
        race = conn.execute(build_get_race_query(race_id)).one_or_none()
        racers = conn.execute(build_get_race_racers_query(race_id))
        if race and racers:
            return race, list(racers)
    return None, []


def search_racers(make: str, model: str, year: str) -> list[Row]:
    if make:
        with db.connect() as conn:
            return list(
                conn.execute(
                    build_search_racer_query(make, model, year).limit(
                        _MAX_SEARCH_RESULT
                    )
                )
            )
    return []


def save_race(model_ids: list[int]) -> tuple[None | Row, list[Row]]:
    with db.connect() as conn:
        race = conn.execute(build_insert_race_query())
        race_id = race.lastrowid
        conn.execute(build_insert_race_racers_query(race_id, model_ids))
        conn.commit()
        return get_race(race_id)


def get_popular_pairs() -> list[tuple[None | Row, list[Row]]]:
    pairs = []
    with db.connect() as conn:
        results = conn.execute(build_popular_pairs_query(_MAX_POPULAR_PAIRS))
        for result in results:
            model_ids = [result.id_1, result.id_2]
            check = conn.execute(build_check_race_by_racers_query(model_ids)).first()
            if check:
                pairs.append(get_race(check.race_id))
            else:
                pairs.append(save_race(model_ids))
    return pairs


def get_recent_races() -> list[tuple[None | Row, list[Row]]]:
    races = []
    with db.connect() as conn:
        results = conn.execute(build_most_recent_races_query().limit(_MAX_RECENT_RACES))
        for result in results:
            races.append(get_race(result.id))
    return races

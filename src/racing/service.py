import hashlib

from sqlalchemy import Row

from src.database import engine as db
from src.racing.queries import (
    build_check_race_by_racers_query,
    build_check_user_vote_query,
    build_get_race_downvotes_query,
    build_get_race_query,
    build_get_race_racers_query,
    build_get_race_upvotes_query,
    build_get_racer_by_make_model_query,
    build_insert_race_query,
    build_insert_race_racers_query,
    build_insert_race_unique_query,
    build_most_recent_races_query,
    build_popular_pairs_query,
    build_search_racer_makes_query,
    build_search_racer_query,
    build_vote_race_query,
)

_MAX_SEARCH_RESULT = 10
_MAX_RECENT_RACES = 30
_MAX_POPULAR_PAIRS = 10
_MAKE_SEARCH_PATCHES = {
    "harley": "harley-davidson",
    "harley davidson": "harley-davidson",
    "royal": "enfield",
    "royal enfield": "enfield",
}


def make_unique_race_id(model_ids: list[int]) -> str:
    return hashlib.md5("".join(map(str, sorted(model_ids))).encode()).hexdigest()


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
    if make.lower() in _MAKE_SEARCH_PATCHES:
        make = _MAKE_SEARCH_PATCHES[make.lower()]
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


def search_racer_makes(make: str) -> list[str]:
    with db.connect() as conn:
        return [
            row.name
            for row in conn.execute(
                build_search_racer_makes_query(make).limit(_MAX_SEARCH_RESULT)
            )
        ]


def save_race(
    model_ids: list[int], user_id: None | int = None
) -> tuple[None | Row, list[Row]]:
    with db.connect() as conn:
        race_unique_id = make_unique_race_id(model_ids)
        conn.execute(build_insert_race_unique_query(race_unique_id))
        race = conn.execute(build_insert_race_query(race_unique_id, user_id))

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
            race_unique_id = make_unique_race_id(model_ids)
            check = conn.execute(
                build_check_race_by_racers_query(race_unique_id)
            ).first()
            if check:
                pairs.append(get_race(check.id))
            else:
                pairs.append(save_race(model_ids))
    return pairs


def get_recent_races(user_id: int | None = None) -> list[tuple[None | Row, list[Row]]]:
    races = []
    with db.connect() as conn:
        results = conn.execute(
            build_most_recent_races_query(user_id).limit(_MAX_RECENT_RACES)
        )
        for result in results:
            races.append(get_race(result.id))
    return races


def get_votes(race_unique_id: str) -> None | tuple[int, int]:
    with db.connect() as conn:
        upvotes = conn.execute(
            build_get_race_upvotes_query(race_unique_id)
        ).one_or_none()
        if not upvotes:
            return None
        downvotes = conn.execute(
            build_get_race_downvotes_query(race_unique_id)
        ).one_or_none()
        if not downvotes:
            return None
    return upvotes.count, downvotes.count


def user_has_voted(race_unique_id: str, user_id: int) -> bool:
    with db.connect() as conn:
        return bool(
            conn.execute(
                build_check_user_vote_query(race_unique_id, user_id)
            ).one_or_none()
        )


def vote_race(race_unique_id: str, user_id: int, vote: int) -> bool:
    with db.connect() as conn:
        if not user_has_voted(race_unique_id, user_id):
            conn.execute(build_vote_race_query(race_unique_id, user_id, vote))
            conn.commit()
            return True
        else:
            return False

from sqlalchemy import Row
from typing import Generator
from database import engine as db
from racing.queries import (
  build_get_race_query,
  build_get_racer_by_make_model_query,
  build_insert_race_query,
  build_insert_race_racers_query,
  build_search_racer_query,
  build_popular_pairs_query,
  build_most_recent_races_query,
)


_MAX_SEARCH_RESULT = 20
_MAX_RACERS_PER_RACE = 10
_MAX_RECENT_RACES = 30


def get_racer(make: str, model: str) -> Row | None:
  if make and model:
    with db.connect() as conn:
        return conn.execute(
          build_get_racer_by_make_model_query(make, model)
        ).first()


def get_race(race_id: int) -> list[Row]:
    with db.connect() as conn:
      return list(
        conn.execute(build_get_race_query(race_id).limit(_MAX_RACERS_PER_RACE))
      )


def search_racers(
  make: str, model: str
) -> list[Row]:
  if make:
    with db.connect() as conn:
      return conn.execute(
        build_search_racer_query(make, model).limit(_MAX_SEARCH_RESULT)
      )
  return ()


def save_race(model_ids: list[int]) -> int | None:
  if model_ids:
    with db.connect() as conn:
      race = conn.execute(build_insert_race_query())
      race_id = race.lastrowid
      conn.execute(build_insert_race_racers_query(race_id, model_ids))
      conn.commit()
      return race_id


def get_popular_pairs() -> Generator[tuple[dict, dict, int], None, None]:
  with db.connect() as conn:
    results = conn.execute(build_popular_pairs_query())
    for result in results:
      data = result._asdict()
      racer_1 = {}
      racer_2 = {}
      for key, value in data.items():
        if key.endswith('_1'):
          racer_1[key.replace('_1', '')] = value
        elif key.endswith('_2'):
          racer_2[key.replace('_2', '')] = value
      yield (racer_1, racer_2, data['occurence'])


def get_recent_races() -> Generator[list[Row], None, None]:
  with db.connect() as conn:
    results = conn.execute(
      build_most_recent_races_query().limit(_MAX_RECENT_RACES)
    )
    for result in results:
      yield get_race(result.id)

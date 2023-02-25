from typing import Generator, cast

import pytest
from sqlalchemy import Connection, Row, text

from src.racing.models import Race, RaceListing, Racer, SaveRequest
from src.racing.routes import insight_popular_pairs, insight_recent_races
from src.racing.routes import race as route_race
from src.racing.routes import racer as route_racer
from src.racing.routes import save as route_save
from src.racing.routes import search as route_search
from tests.dummy_data import TEST_DATA_MAKES, TEST_DATA_MODELS
from tests.factories import make_auth_optional, store_user, store_user_session


@pytest.fixture(scope="function", autouse=True)
def clear_racers(db: Connection) -> Generator:
    yield
    db.execute(text("DELETE FROM race_racers"))
    db.execute(text("DELETE FROM race_history"))
    db.execute(text("ALTER TABLE race_history AUTO_INCREMENT = 1"))
    db.commit()


def _store_race(
    db: Connection, model_ids: list[int], user_id: None | int = None
) -> int:
    if user_id:
        result = db.execute(
            text(f"INSERT INTO race_history (user_id) VALUES({user_id})")
        )
    else:
        result = db.execute(text(f"INSERT INTO race_history VALUES()"))
    race_id = cast(int, result.lastrowid)
    for model_id in model_ids:
        db.execute(text(f"INSERT INTO race_racers VALUES({race_id}, {model_id})"))
    db.commit()
    return race_id


def _racer_from_data(model_id: int) -> Racer:
    data = TEST_DATA_MODELS[model_id]
    make_name = TEST_DATA_MAKES[cast(int, data["make"])]
    return Racer(
        **data,
        model_id=model_id,
        make_name=make_name,
        full_name=f'{make_name} {data["name"]}',
    )


#############
### TESTS ###
#############


@pytest.mark.parametrize(
    "make,model,year,expected",
    (
        ("MakeA", "Name 1", "", _racer_from_data(1)),
        ("MakeA", "Name 1", "2022", _racer_from_data(1)),
        ("MakeA", "Name 1", "2023", None),
        ("MakeA", "Nam", "", None),
        ("MakeB", "Name 1", "", None),
        ("", "Name 1", "", None),
        ("", "", "", None),
    ),
)
@pytest.mark.asyncio
async def test_racer(
    db: Connection, make: str, model: str, year: str, expected: Row | None
) -> None:
    # When
    result = await route_racer(make=make, model=model, year=year)

    # Then
    assert result == expected


@pytest.mark.asyncio
async def test_race(db: Connection) -> None:
    # Given
    race_id_1 = _store_race(db, [3, 2])
    _store_race(db, [1, 2])

    # When
    result = await route_race(race_id_1)

    # Then
    assert result == Race(
        race_id=race_id_1,
        racers=[
            _racer_from_data(3),
            _racer_from_data(2),
        ],
    )


@pytest.mark.asyncio
async def test_race_not_found(db: Connection) -> None:
    # When
    result = await route_race(2)

    # Then
    assert result == None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "make,model,year,expected",
    (
        ("MakeA", "Name 1", "", [_racer_from_data(1)]),
        (
            "MakeA",
            "Nam",
            "",
            [
                _racer_from_data(1),
                _racer_from_data(2),
            ],
        ),
        (
            "MakeC",
            "",
            "",
            [
                _racer_from_data(4),
                _racer_from_data(5),
                _racer_from_data(6),
            ],
        ),
        ("Make", "Name 1", "2022", [_racer_from_data(1)]),
        ("MakeB", "Name 1", "", []),
        ("", "Name 1", "", []),
        ("", "", "", []),
    ),
)
async def test_search(
    db: Connection, make: str, model: str, year: str, expected: Row | None
) -> None:
    # When
    result = await route_search(make=make, model=model, year=year)

    # Then
    assert result == expected


@pytest.mark.asyncio
async def test_save(db: Connection) -> None:
    # Given
    request = SaveRequest(model_ids=[1, 2])

    # When
    result = await route_save(request, user=None)

    # Then
    assert result == Race(
        race_id=1,
        racers=[_racer_from_data(1), _racer_from_data(2)],
    )


@pytest.mark.asyncio
async def test_save_with_user(db: Connection) -> None:
    # Given
    user_id = store_user(db)
    token = store_user_session(db, user_id)
    request = SaveRequest(model_ids=[1, 2])

    # When
    result = await route_save(request, user=make_auth_optional(token))

    # Then
    assert result == Race(
        race_id=1,
        racers=[_racer_from_data(1), _racer_from_data(2)],
        user_id=user_id,
    )


@pytest.mark.asyncio
async def test_get_popular_pairs(db: Connection) -> None:
    # Given
    _store_race(db, [3, 2])
    _store_race(db, [3, 4])
    _store_race(db, [3, 2, 1])
    _store_race(db, [3, 6, 2])
    _store_race(db, [1, 2])

    # When
    results = await insight_popular_pairs()

    # Then
    assert results == RaceListing(
        races=[
            Race(
                race_id=1,
                racers=[
                    _racer_from_data(3),
                    _racer_from_data(2),
                ],
            ),
            Race(
                race_id=5,
                racers=[
                    _racer_from_data(1),
                    _racer_from_data(2),
                ],
            ),
        ],
    )


@pytest.mark.asyncio
async def test_get_popular_pairs_creates_race(db: Connection) -> None:
    # Given
    _store_race(db, [3, 2, 5])
    _store_race(db, [3, 4])
    _store_race(db, [3, 2, 1])
    _store_race(db, [3, 6, 2])
    _store_race(db, [1, 2])

    # When
    results = await insight_popular_pairs()

    # Then
    assert results == RaceListing(
        races=[
            Race(
                race_id=6,  # Created
                racers=[
                    _racer_from_data(2),
                    _racer_from_data(3),
                ],
            ),
            Race(
                race_id=5,
                racers=[
                    _racer_from_data(1),
                    _racer_from_data(2),
                ],
            ),
        ],
    )


@pytest.mark.asyncio
async def test_get_popular_pairs_multi_same_race(db: Connection) -> None:
    # Given
    _store_race(db, [1, 3, 5])
    _store_race(db, [3, 4, 1])
    _store_race(db, [3, 5, 1])
    _store_race(db, [3, 1, 2])
    _store_race(db, [1, 5])

    # When
    results = await insight_popular_pairs()

    # Then
    assert results == RaceListing(
        races=[
            Race(
                race_id=6,  # Created
                racers=[
                    _racer_from_data(1),
                    _racer_from_data(3),
                ],
            ),
            Race(
                race_id=5,
                racers=[
                    _racer_from_data(1),
                    _racer_from_data(5),
                ],
            ),
            Race(
                race_id=7,  # Created
                racers=[
                    _racer_from_data(3),
                    _racer_from_data(5),
                ],
            ),
        ],
    )


@pytest.mark.asyncio
async def test_get_recent_races(db: Connection) -> None:
    _store_race(db, [1, 3, 5])
    _store_race(db, [3, 4, 1])
    _store_race(db, [3, 5, 1])

    # When
    results = await insight_recent_races()

    # Then
    assert results == RaceListing(
        races=[
            Race(
                race_id=1,
                racers=[
                    _racer_from_data(1),
                    _racer_from_data(3),
                    _racer_from_data(5),
                ],
            ),
            Race(
                race_id=2,
                racers=[
                    _racer_from_data(3),
                    _racer_from_data(4),
                    _racer_from_data(1),
                ],
            ),
            Race(
                race_id=3,
                racers=[
                    _racer_from_data(3),
                    _racer_from_data(5),
                    _racer_from_data(1),
                ],
            ),
        ],
    )


@pytest.mark.asyncio
async def test_get_recent_races_with_user(db: Connection) -> None:
    # Given
    user_id = store_user(db)
    _store_race(db, [1, 3, 5], user_id=user_id)
    _store_race(db, [3, 4, 1], user_id=user_id)
    _store_race(db, [3, 5, 1])

    # When
    results = await insight_recent_races(user_id)

    # Then
    assert results == RaceListing(
        races=[
            Race(
                race_id=1,
                racers=[
                    _racer_from_data(1),
                    _racer_from_data(3),
                    _racer_from_data(5),
                ],
                user_id=user_id,
            ),
            Race(
                race_id=2,
                racers=[
                    _racer_from_data(3),
                    _racer_from_data(4),
                    _racer_from_data(1),
                ],
                user_id=user_id,
            ),
        ],
    )

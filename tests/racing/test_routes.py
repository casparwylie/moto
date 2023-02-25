from sqlalchemy import text
from typing import cast
import pytest

from src.racing.routes import (
    racer as route_racer,
    race as route_race,
    save as route_save,
    search as route_search,
    insight_popular_pairs,
    insight_recent_races,
)

from src.racing.models import (
    Race,
    Racer,
    RaceListing,
    SaveRequest,
)

from tests.dummy_data import TEST_DATA_MODELS, TEST_DATA_MAKES


@pytest.fixture(scope="function", autouse=True)
def clear_racers(db):
    yield
    db.execute(text("DELETE FROM race_racers"))
    db.execute(text("DELETE FROM race_history"))
    db.execute(text("ALTER TABLE race_history AUTO_INCREMENT = 1"))
    db.commit()


def _store_race(db, model_ids: list[int]) -> int:
    result = db.execute(text("INSERT INTO race_history VALUES()"))
    race_id = cast(int, result.lastrowid)
    for model_id in model_ids:
        db.execute(text(f"INSERT INTO race_racers VALUES({race_id}, {model_id})"))
    db.commit()
    return race_id


def racer_from_data(model_id):
    data = TEST_DATA_MODELS[model_id]
    make_name = TEST_DATA_MAKES[data["make"]]
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
        ("MakeA", "Name 1", "", racer_from_data(1)),
        ("MakeA", "Name 1", "2022", racer_from_data(1)),
        ("MakeA", "Name 1", "2023", None),
        ("MakeA", "Nam", "", None),
        ("MakeB", "Name 1", "", None),
        ("", "Name 1", "", None),
        ("", "", "", None),
    ),
)
@pytest.mark.asyncio
async def test_racer(db, make, model, year, expected):
    # When
    result = await route_racer(make=make, model=model, year=year)

    # Then
    assert result == expected


@pytest.mark.asyncio
async def test_race(db):
    # Given
    race_id_1 = _store_race(db, [3, 2])
    race_id_2 = _store_race(db, [1, 2])

    # When
    result = await route_race(race_id_1)

    # Then
    assert result == Race(
        race_id=race_id_1,
        racers=[
            racer_from_data(3),
            racer_from_data(2),
        ],
    )


@pytest.mark.asyncio
async def test_race_not_found(db):
    # When
    result = await route_race(2)

    # Then
    assert result == None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "make,model,year,expected",
    (
        ("MakeA", "Name 1", "", [racer_from_data(1)]),
        (
            "MakeA",
            "Nam",
            "",
            [
                racer_from_data(1),
                racer_from_data(2),
            ],
        ),
        (
            "MakeC",
            "",
            "",
            [
                racer_from_data(4),
                racer_from_data(5),
                racer_from_data(6),
            ],
        ),
        ("Make", "Name 1", "2022", [racer_from_data(1)]),
        ("MakeB", "Name 1", "", []),
        ("", "Name 1", "", []),
        ("", "", "", []),
    ),
)
async def test_search(db, make, model, year, expected):
    # When
    result = await route_search(make=make, model=model, year=year)

    # Then
    assert result == expected


@pytest.mark.asyncio
async def test_save(db):
    # Given
    request = SaveRequest(model_ids=[1, 2])

    # When
    result = await route_save(request)

    # Then
    assert result == Race(
        race_id=1,
        racers=[racer_from_data(1), racer_from_data(2)],
    )


@pytest.mark.asyncio
async def test_get_popular_pairs(db):
    # Given
    race_id_1 = _store_race(db, [3, 2])
    race_id_2 = _store_race(db, [3, 4])
    race_id_3 = _store_race(db, [3, 2, 1])
    race_id_4 = _store_race(db, [3, 6, 2])
    race_id_5 = _store_race(db, [1, 2])

    # When
    results = await insight_popular_pairs()

    # Then
    assert results == RaceListing(
        races=[
            Race(
                race_id=1,
                racers=[
                    racer_from_data(3),
                    racer_from_data(2),
                ],
            ),
            Race(
                race_id=5,
                racers=[
                    racer_from_data(1),
                    racer_from_data(2),
                ],
            ),
        ],
    )


@pytest.mark.asyncio
async def test_get_popular_pairs_creates_race(db):
    # Given
    race_id_1 = _store_race(db, [3, 2, 5])
    race_id_2 = _store_race(db, [3, 4])
    race_id_3 = _store_race(db, [3, 2, 1])
    race_id_4 = _store_race(db, [3, 6, 2])
    race_id_5 = _store_race(db, [1, 2])

    # When
    results = await insight_popular_pairs()

    # Then
    assert results == RaceListing(
        races=[
            Race(
                race_id=6,  # Created
                racers=[
                    racer_from_data(2),
                    racer_from_data(3),
                ],
            ),
            Race(
                race_id=5,
                racers=[
                    racer_from_data(1),
                    racer_from_data(2),
                ],
            ),
        ],
    )


@pytest.mark.asyncio
async def test_get_popular_pairs_multi_same_race(db):
    # Given
    race_id_1 = _store_race(db, [1, 3, 5])
    race_id_2 = _store_race(db, [3, 4, 1])
    race_id_3 = _store_race(db, [3, 5, 1])
    race_id_4 = _store_race(db, [3, 1, 2])
    race_id_5 = _store_race(db, [1, 5])

    # When
    results = await insight_popular_pairs()

    # Then
    assert results == RaceListing(
        races=[
            Race(
                race_id=6,  # Created
                racers=[
                    racer_from_data(1),
                    racer_from_data(3),
                ],
            ),
            Race(
                race_id=5,
                racers=[
                    racer_from_data(1),
                    racer_from_data(5),
                ],
            ),
            Race(
                race_id=7,  # Created
                racers=[
                    racer_from_data(3),
                    racer_from_data(5),
                ],
            ),
        ],
    )


@pytest.mark.asyncio
async def test_get_recent_races(db):
    race_id_1 = _store_race(db, [1, 3, 5])
    race_id_2 = _store_race(db, [3, 4, 1])
    race_id_3 = _store_race(db, [3, 5, 1])

    # When
    results = await insight_recent_races()

    # Then
    assert results == RaceListing(
        races=[
            Race(
                race_id=1,
                racers=[
                    racer_from_data(1),
                    racer_from_data(3),
                    racer_from_data(5),
                ],
            ),
            Race(
                race_id=2,
                racers=[
                    racer_from_data(3),
                    racer_from_data(4),
                    racer_from_data(1),
                ],
            ),
            Race(
                race_id=3,
                racers=[
                    racer_from_data(3),
                    racer_from_data(5),
                    racer_from_data(1),
                ],
            ),
        ],
    )

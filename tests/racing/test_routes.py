from typing import Generator, cast

import pytest
from fastapi import HTTPException
from sqlalchemy import Connection, Row, text

from src.racing.models import (
    Race,
    RaceListing,
    Racer,
    RaceVoteRequest,
    RaceVotesResponse,
    SaveRequest,
    SuccessResponse,
)
from src.racing.routes import (
    _get_insight_popular_pairs,
    _get_insight_recent_races,
    _get_race,
    _get_racer,
    _get_voted,
    _get_votes,
    _save_race,
    _search_racer_makes,
    _search_racers,
    _vote_race,
)
from src.racing.service import make_unique_race_id
from tests.dummy_data import TEST_DATA_MAKES, TEST_DATA_MODELS
from tests.factories import (
    make_auth_optional,
    make_auth_required,
    store_race,
    store_user,
    store_user_session,
)


@pytest.fixture(scope="function", autouse=True)
def clear_racers(db: Connection) -> Generator:
    yield
    db.execute(text("DELETE FROM race_racers"))
    db.execute(text("DELETE FROM race_votes"))
    db.execute(text("DELETE FROM race_history"))
    db.execute(text("ALTER TABLE race_history AUTO_INCREMENT = 1"))
    db.execute(text("DELETE FROM race_unique"))
    db.commit()


def _racer_from_data(model_id: int) -> Racer:
    data = TEST_DATA_MODELS[model_id]
    make_name = TEST_DATA_MAKES[cast(int, data["make"])]
    return Racer(
        **data,
        model_id=model_id,
        make_name=make_name,
        full_name=f'{make_name} {data["name"]}',
    )


def _store_race_vote(
    db: Connection, race_unique_id: str, user_id: int, vote: int
) -> None:
    db.execute(
        text(f"INSERT INTO race_votes VALUES('{race_unique_id}', {user_id}, {vote})")
    )
    db.commit()


def _get_race_unique(db: Connection, race_unique_id: str) -> Row:
    return db.execute(
        text(f"SELECT * FROM race_unique WHERE id='{race_unique_id}'")
    ).all()


def _get_race_votes(db: Connection, race_unique_id: str) -> Row:
    return db.execute(
        text(f"SELECT * FROM race_votes WHERE race_unique_id='{race_unique_id}'")
    ).all()


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
async def test_get_racer(
    db: Connection, make: str, model: str, year: str, expected: Row | None
) -> None:
    # When
    result = await _get_racer(make=make, model=model, year=year)

    # Then
    assert result == expected


@pytest.mark.asyncio
async def test_get_race(db: Connection) -> None:
    # Given
    race_id_1, race_unique_id_1 = store_race(db, [3, 2])
    store_race(db, [1, 2])

    # When
    result = await _get_race(race_id_1)

    # Then
    assert result == Race(
        race_id=race_id_1,
        race_unique_id=race_unique_id_1,
        racers=[
            _racer_from_data(3),
            _racer_from_data(2),
        ],
    )


@pytest.mark.asyncio
async def test_get_race_not_found(db: Connection) -> None:
    with pytest.raises(HTTPException):
        await _get_race(2)


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
        # Search patch cases...
        ("MakeA", "Name1", "", [_racer_from_data(1)]),
        ("MakeA", "Name-1", "", [_racer_from_data(1)]),
    ),
)
async def test_search_racers(
    make: str, model: str, year: str, expected: Row | None
) -> None:
    # When
    result = await _search_racers(make=make, model=model, year=year)

    # Then
    assert result == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "make,expected",
    (
        ("Make", ["MakeA", "MakeB", "MakeC"]),
        ("MakeA", ["MakeA"]),
        ("", ["MakeA", "MakeB", "MakeC"]),
    ),
)
async def test_search_racer_makes(
    db: Connection, make: str, expected: list[str]
) -> None:
    # When
    result = await _search_racer_makes(make=make)

    # Then
    assert result.makes == expected


@pytest.mark.asyncio
async def test_save_race(db: Connection) -> None:
    # Given
    request = SaveRequest(model_ids=[1, 2])
    race_unique_id = make_unique_race_id([1, 2])
    # When
    result = await _save_race(request, user=None)

    # Then
    assert len(_get_race_unique(db, race_unique_id)) == 1
    assert result == Race(
        race_id=1,
        racers=[_racer_from_data(1), _racer_from_data(2)],
        race_unique_id=race_unique_id,
    )


@pytest.mark.asyncio
async def test_save_race_multi_same_models(db: Connection) -> None:
    # Given
    request = SaveRequest(model_ids=[1, 2])
    race_unique_id = make_unique_race_id([1, 2])

    # When
    result_1 = await _save_race(request, user=None)
    result_2 = await _save_race(request, user=None)

    # Then
    assert len(_get_race_unique(db, race_unique_id)) == 1
    assert result_1 == Race(
        race_id=1,
        racers=[_racer_from_data(1), _racer_from_data(2)],
        race_unique_id=race_unique_id,
    )
    assert result_2 == Race(
        race_id=2,
        racers=[_racer_from_data(1), _racer_from_data(2)],
        race_unique_id=race_unique_id,
    )


@pytest.mark.asyncio
async def test_save_race_multi_different_models(db: Connection) -> None:
    # Given
    request_1 = SaveRequest(model_ids=[1, 2])
    request_2 = SaveRequest(model_ids=[1, 3])
    race_unique_id_1 = make_unique_race_id([1, 2])
    race_unique_id_2 = make_unique_race_id([1, 3])

    # When
    result_1 = await _save_race(request_1, user=None)
    result_2 = await _save_race(request_2, user=None)

    # Then
    assert len(_get_race_unique(db, race_unique_id_1)) == 1
    assert len(_get_race_unique(db, race_unique_id_2)) == 1
    assert result_1 == Race(
        race_id=1,
        racers=[_racer_from_data(1), _racer_from_data(2)],
        race_unique_id=race_unique_id_1,
    )
    assert result_2 == Race(
        race_id=2,
        racers=[_racer_from_data(1), _racer_from_data(3)],
        race_unique_id=race_unique_id_2,
    )


@pytest.mark.asyncio
async def test_save_race_with_user(db: Connection) -> None:
    # Given
    user_id = store_user(db)
    token = store_user_session(db, user_id)
    request = SaveRequest(model_ids=[1, 2, 3])
    expected_race_unique_id = make_unique_race_id([1, 2, 3])

    # When
    result = await _save_race(request, user=make_auth_optional(token))

    # Then
    assert _get_race_unique(db, expected_race_unique_id)
    assert result == Race(
        race_id=1,
        racers=[_racer_from_data(1), _racer_from_data(2), _racer_from_data(3)],
        user_id=user_id,
        race_unique_id=expected_race_unique_id,
    )


@pytest.mark.asyncio
async def test_get_popular_pairs(db: Connection) -> None:
    # Given
    race_id_1, race_unique_id_1 = store_race(db, [3, 2])
    store_race(db, [3, 4])
    store_race(db, [3, 2, 1])
    store_race(db, [3, 6, 2])
    race_id_2, race_unique_id_2 = store_race(db, [1, 2])

    # When
    results = await _get_insight_popular_pairs()

    # Then
    assert results == RaceListing(
        races=[
            Race(
                race_id=race_id_1,
                race_unique_id=race_unique_id_1,
                racers=[
                    _racer_from_data(3),
                    _racer_from_data(2),
                ],
            ),
            Race(
                race_id=race_id_2,
                race_unique_id=race_unique_id_2,
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
    store_race(db, [3, 2, 5])
    store_race(db, [3, 4])
    store_race(db, [3, 2, 1])
    store_race(db, [3, 6, 2])
    race_id, race_unique_id_1 = store_race(db, [1, 2])

    # When
    results = await _get_insight_popular_pairs()

    # Then
    assert results == RaceListing(
        races=[
            Race(
                race_id=6,  # Created
                race_unique_id=make_unique_race_id([2, 3]),
                racers=[
                    _racer_from_data(2),
                    _racer_from_data(3),
                ],
            ),
            Race(
                race_id=race_id,
                race_unique_id=race_unique_id_1,
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
    store_race(db, [1, 3, 5])
    store_race(db, [3, 4, 1])
    store_race(db, [3, 5, 1])
    store_race(db, [3, 1, 2])
    race_id, race_unique_id = store_race(db, [1, 5])

    # When
    results = await _get_insight_popular_pairs()

    # Then
    assert results == RaceListing(
        races=[
            Race(
                race_id=6,  # Created
                race_unique_id=make_unique_race_id([1, 3]),
                racers=[
                    _racer_from_data(1),
                    _racer_from_data(3),
                ],
            ),
            Race(
                race_id=race_id,
                race_unique_id=race_unique_id,
                racers=[
                    _racer_from_data(1),
                    _racer_from_data(5),
                ],
            ),
            Race(
                race_id=7,  # Created
                race_unique_id=make_unique_race_id([3, 5]),
                racers=[
                    _racer_from_data(3),
                    _racer_from_data(5),
                ],
            ),
        ],
    )


@pytest.mark.asyncio
async def test_get_recent_races(db: Connection) -> None:
    race_id_1, race_unique_id_1 = store_race(db, [1, 3, 5])
    race_id_2, race_unique_id_2 = store_race(db, [3, 4, 1])
    race_id_3, race_unique_id_3 = store_race(db, [3, 5, 1])

    # When
    results = await _get_insight_recent_races()

    # Then
    assert results == RaceListing(
        races=[
            Race(
                race_id=race_id_1,
                race_unique_id=race_unique_id_1,
                racers=[
                    _racer_from_data(1),
                    _racer_from_data(3),
                    _racer_from_data(5),
                ],
            ),
            Race(
                race_id=race_id_2,
                race_unique_id=race_unique_id_2,
                racers=[
                    _racer_from_data(3),
                    _racer_from_data(4),
                    _racer_from_data(1),
                ],
            ),
            Race(
                race_id=race_id_3,
                race_unique_id=race_unique_id_3,
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
    race_id_1, race_unique_id_1 = store_race(db, [1, 3, 5], user_id=user_id)
    race_id_2, race_unique_id_2 = store_race(db, [3, 4, 1], user_id=user_id)
    store_race(db, [3, 5, 1])

    # When
    results = await _get_insight_recent_races(user_id)

    # Then
    assert results == RaceListing(
        races=[
            Race(
                race_id=race_id_1,
                race_unique_id=race_unique_id_1,
                racers=[
                    _racer_from_data(1),
                    _racer_from_data(3),
                    _racer_from_data(5),
                ],
                user_id=user_id,
            ),
            Race(
                race_id=race_id_2,
                race_unique_id=race_unique_id_2,
                racers=[
                    _racer_from_data(3),
                    _racer_from_data(4),
                    _racer_from_data(1),
                ],
                user_id=user_id,
            ),
        ],
    )


@pytest.mark.asyncio
async def test_get_votes(db: Connection) -> None:
    # Given
    user_id_1 = store_user(db)
    user_id_2 = store_user(db)
    user_id_3 = store_user(db)
    race_id, race_unique_id = store_race(db, [1, 2])
    _store_race_vote(db, race_unique_id, user_id_1, 1)
    _store_race_vote(db, race_unique_id, user_id_2, 1)
    _store_race_vote(db, race_unique_id, user_id_3, 0)

    # When
    results = await _get_votes(race_unique_id)

    # Then
    assert results == RaceVotesResponse(upvotes=2, downvotes=1)


@pytest.mark.asyncio
async def test_vote_race(db: Connection) -> None:
    # Given
    user_id = store_user(db)
    token = store_user_session(db, user_id)
    race_id, race_unique_id = store_race(db, [1, 2])
    vote_request = RaceVoteRequest(race_unique_id=race_unique_id, vote=1)

    # When
    result = await _vote_race(vote_request, user=make_auth_required(token))
    assert result == SuccessResponse(success=True)

    votes = _get_race_votes(db, race_unique_id)
    assert votes[0].vote == vote_request.vote
    assert len(votes) == 1


@pytest.mark.asyncio
async def test_vote_race_already_voted(db: Connection) -> None:
    # Given
    user_id = store_user(db)
    token = store_user_session(db, user_id)
    race_id, race_unique_id = store_race(db, [1, 2])
    _store_race_vote(db, race_unique_id, user_id, 1)
    vote_request = RaceVoteRequest(race_unique_id=race_unique_id, vote=1)

    # When
    result = await _vote_race(vote_request, user=make_auth_required(token))
    assert result == SuccessResponse(success=False)

    votes = _get_race_votes(db, race_unique_id)
    assert len(votes) == 1


@pytest.mark.asyncio
async def test_vote_multiple_users_and_get(db: Connection) -> None:
    # Given
    race_id, race_unique_id = store_race(db, [1, 2])

    user_id_1 = store_user(db)
    user_id_2 = store_user(db)
    user_id_3 = store_user(db)

    token_1 = store_user_session(db, user_id_1)
    token_2 = store_user_session(db, user_id_2)
    token_3 = store_user_session(db, user_id_3)

    vote_request_1 = RaceVoteRequest(race_unique_id=race_unique_id, vote=1)
    vote_request_2 = RaceVoteRequest(race_unique_id=race_unique_id, vote=0)
    vote_request_3 = RaceVoteRequest(race_unique_id=race_unique_id, vote=1)

    # When
    await _vote_race(vote_request_1, user=make_auth_required(token_1))
    await _vote_race(vote_request_2, user=make_auth_required(token_2))
    await _vote_race(vote_request_3, user=make_auth_required(token_3))

    await _vote_race(vote_request_3, user=make_auth_required(token_3))

    race_votes = await _get_votes(race_unique_id)

    # Then
    assert race_votes == RaceVotesResponse(upvotes=2, downvotes=1)


@pytest.mark.asyncio
async def test_user_voted(db: Connection) -> None:
    # Given
    race_id, race_unique_id = store_race(db, [1, 2])

    user_id = store_user(db)
    token = store_user_session(db, user_id)

    _store_race_vote(db, race_unique_id, user_id, 1)

    result = await _get_voted(race_unique_id, user=make_auth_required(token))

    assert result.voted is True

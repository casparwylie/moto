from datetime import datetime
from typing import Generator, cast

import pytest
from fastapi import HTTPException
from freezegun.api import FrozenDateTimeFactory
from sqlalchemy import Connection, Row, text

from src.social.models import (
    AddCommentRequest,
    Comment,
    CommentsResponse,
    DeleteCommentRequest,
    SuccessResponse,
)
from src.social.routes import _add_comment, _delete_comment, _get_comments
from tests.dummy_data import TEST_DATA_MAKES, TEST_DATA_MODELS
from tests.factories import (
    make_auth_optional,
    make_auth_required,
    store_garage_item,
    store_race,
    store_user,
    store_user_session,
)


@pytest.fixture(scope="function", autouse=True)
def clear_comments(db: Connection) -> Generator:
    yield
    db.execute(text("DELETE FROM race_racers"))
    db.execute(text("DELETE FROM race_history"))
    db.execute(text("ALTER TABLE race_history AUTO_INCREMENT = 1"))
    db.execute(text("DELETE FROM race_comments"))
    db.execute(text("DELETE FROM race_unique"))
    db.commit()


_insert_comment_query = """
  INSERT INTO race_comments (text, race_unique_id, user_id, created_at)
  VALUES ('{text}', '{race_unique_id}', {user_id}, {created_at})
"""


def _store_comment(
    db: Connection,
    user_id: int,
    race_unique_id: str,
    txt: str = "Comment text",
) -> int:
    created_at = int(datetime.timestamp(datetime.now()))
    result = db.execute(
        text(
            _insert_comment_query.format(
                text=txt,
                user_id=user_id,
                race_unique_id=race_unique_id,
                created_at=created_at,
            )
        )
    )
    db.commit()
    return cast(int, result.lastrowid)


def _get_first_comment(db: Connection) -> Row:
    return db.execute(text("SELECT * FROM race_comments")).first()


#############
### TESTS ###
#############


@pytest.mark.asyncio
async def test_add_comment(db: Connection, freezer: FrozenDateTimeFactory) -> None:
    # Given
    user_id = store_user(db)
    token = store_user_session(db, user_id)
    race_id, race_unique_id = store_race(db, [1, 2])
    add_comment_request = AddCommentRequest(
        race_unique_id=race_unique_id, text="Comment text"
    )

    # When
    result = await _add_comment(add_comment_request, user=make_auth_required(token))

    # Then
    expected_created_at = int(datetime.timestamp(datetime.now()))
    comment = _get_first_comment(db)
    assert result.success
    assert comment.text == add_comment_request.text
    assert comment.race_unique_id == add_comment_request.race_unique_id
    assert comment.user_id == user_id
    assert comment.created_at == expected_created_at


@pytest.mark.asyncio
async def test_delete_comment(db: Connection) -> None:
    # Given
    user_id = store_user(db)
    token = store_user_session(db, user_id)
    race_id, race_unique_id = store_race(db, [1, 2])
    comment_id = _store_comment(db, user_id, race_unique_id)
    delete_comment_request = DeleteCommentRequest(comment_id=comment_id)

    # When
    result = await _delete_comment(
        delete_comment_request, user=make_auth_required(token)
    )

    # Then
    assert not _get_first_comment(db)
    assert result.success


@pytest.mark.asyncio
async def test_get_comments(db: Connection, freezer: FrozenDateTimeFactory) -> None:
    # Given
    user_id_1 = store_user(db, username="user1")
    user_id_2 = store_user(db, username="user2")
    race_id, race_unique_id = store_race(db, [1, 2, 3])

    comment_id_1 = _store_comment(db, user_id_1, race_unique_id, txt="Comment 1")
    comment_id_2 = _store_comment(db, user_id_2, race_unique_id, txt="Comment 2")

    store_garage_item(db, user_id_1, 1, "SAT_ON")
    store_garage_item(db, user_id_1, 3, "SAT_ON")
    store_garage_item(db, user_id_1, 2, "HAS_RIDDEN")
    store_garage_item(db, user_id_2, 1, "OWNS")
    store_garage_item(db, user_id_2, 4, "OWNS")  # Ignored

    # When
    result = await _get_comments(race_unique_id)

    # Then
    expected_created_at = datetime.fromtimestamp(
        datetime.timestamp(datetime.now())
    ).strftime("%m/%d/%Y, %H:%M")
    assert result == CommentsResponse(
        comments=[
            Comment(
                id=comment_id_1,
                text="Comment 1",
                username="user1",
                race_unique_id=race_unique_id,
                created_at=expected_created_at,
                garage_relation_sentence="has sat on the Name 1 and the Name 3 and has ridden the Name 2",
            ),
            Comment(
                id=comment_id_2,
                text="Comment 2",
                username="user2",
                race_unique_id=race_unique_id,
                created_at=expected_created_at,
                garage_relation_sentence="currently owns the Name 1",
            ),
        ]
    )

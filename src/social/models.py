from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Row


class SuccessResponse(BaseModel):
    success: bool
    errors: list[str] = []


class AddCommentRequest(BaseModel):
    race_unique_id: str
    text: str


class Comment(BaseModel):
    id: int
    text: str
    username: str
    race_unique_id: str
    created_at: str
    garage_relation_sentence: str = ""

    @classmethod
    def from_service(cls, data: Row, garage_relation_sentence: str) -> "Comment":
        return cls(
            id=data.id,
            text=data.text,
            username=data.username,
            race_unique_id=data.race_unique_id,
            created_at=datetime.fromtimestamp(data.created_at).strftime(
                "%m/%d/%Y, %H:%M"
            ),
            garage_relation_sentence=garage_relation_sentence,
        )


class CommentsResponse(BaseModel):
    comments: list[Comment]

    @classmethod
    def from_service(cls, data: list[tuple[Row, str]]) -> "CommentsResponse":
        return cls(
            comments=[
                Comment.from_service(comment, garage_relation_sentence)
                for comment, garage_relation_sentence in data
            ]
        )


class DeleteCommentRequest(BaseModel):
    comment_id: int

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
    text: str
    username: str
    race_unique_id: str
    created_at: str

    @classmethod
    def from_service(cls, data: Row) -> "Comment":
        return cls(
            text=data.text,
            username=data.username,
            race_unique_id=data.race_unique_id,
            created_at=datetime.fromtimestamp(data.created_at).strftime(
                "%m/%d/%Y, %H:%M"
            ),
        )


class CommentsResponse(BaseModel):
    comments: list[Comment]

    @classmethod
    def from_service(cls, data: list[Row]) -> "CommentsResponse":
        return cls(comments=[Comment.from_service(item) for item in data])

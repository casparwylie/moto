from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, status
from sqlalchemy import Row

from src.auth import auth_optional, auth_required
from src.social.models import AddCommentRequest, CommentsResponse, SuccessResponse
from src.social.service import add_race_comment, get_race_comments
from src.social.validation import invalid_comment_text

router = APIRouter(prefix="/api/social")


@router.post("/add-comment")
async def add_comment(
    request: AddCommentRequest,
    user: Row = Depends(auth_required),
) -> SuccessResponse:
    if err := invalid_comment_text(request.text):
        return SuccessResponse(success=False, errors=[err])
    add_race_comment(request.text, request.race_unique_id, user.id)
    return SuccessResponse(success=True)


@router.get("/comments")
async def get_comments(
    race_unique_id: str,
) -> CommentsResponse:
    return CommentsResponse.from_service(get_race_comments(race_unique_id))

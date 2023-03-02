from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, status
from sqlalchemy import Row

from src.auth import auth_optional, auth_required
from src.social.models import (
    AddCommentRequest,
    CommentsResponse,
    DeleteCommentRequest,
    SuccessResponse,
)
from src.social.service import add_comment, delete_comment, get_comments
from src.social.validation import invalid_comment_text

router = APIRouter(prefix="/api/social")


@router.post("/add-comment")
async def _add_comment(
    request: AddCommentRequest,
    user: Row = Depends(auth_required),
) -> SuccessResponse:
    if err := invalid_comment_text(request.text):
        return SuccessResponse(success=False, errors=[err])
    add_comment(request.text, request.race_unique_id, user.id)
    return SuccessResponse(success=True)


@router.get("/comments")
async def _get_comments(
    race_unique_id: str,
) -> CommentsResponse:
    return CommentsResponse.from_service(get_comments(race_unique_id))


@router.post("/delete-comment")
async def _delete_comment(
    request: DeleteCommentRequest,
    user: Row = Depends(auth_required),
) -> SuccessResponse:
    success = delete_comment(request.comment_id, user.id)
    return SuccessResponse(success=success)

from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException, status
from sqlalchemy import Row

from src.auth import auth_optional, auth_required
from src.racing.models import (
    HasVotedResponse,
    Race,
    RaceListing,
    Racer,
    RaceVoteRequest,
    RaceVotesResponse,
    SaveRequest,
    SuccessResponse,
)
from src.racing.service import (
    get_popular_pairs,
    get_race,
    get_racer,
    get_recent_races,
    get_votes,
    save_race,
    search_racers,
    user_has_voted,
    vote_race,
)

router = APIRouter(prefix="/api/racing")


@router.get("/racer")
async def _get_racer(make: str, model: str, year: str) -> Racer | None:
    if racer := get_racer(make, model, year):
        return Racer.from_db_data(racer)


@router.get("/race")
async def _get_race(race_id: int) -> Race | None:
    race, racers = get_race(race_id)
    if race and racers:
        return Race.from_service(race, racers)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.get("/race/search")
async def _search_racers(make: str, model: str, year: str) -> list[Racer]:
    return [Racer.from_db_data(result) for result in search_racers(make, model, year)]


@router.post("/race/save")
async def _save_race(
    request: SaveRequest, user: None | Row = Depends(auth_optional)
) -> Race | None:
    user_id = user.id if user else None
    race, racers = save_race(request.model_ids, user_id)
    if race and racers:
        return Race.from_service(race, racers)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)


@router.post("/race/vote")
async def _vote_race(
    request: RaceVoteRequest, user: Row = Depends(auth_required)
) -> SuccessResponse:
    if request.vote not in {1, 0}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    success = vote_race(request.race_unique_id, user.id, request.vote)
    return SuccessResponse(success=success)


@router.get("/race/votes")
async def _get_votes(race_unique_id: str) -> RaceVotesResponse:
    if votes := get_votes(race_unique_id):
        return RaceVotesResponse(upvotes=votes[0], downvotes=votes[1])
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.get("/race/vote/voted")
async def _get_voted(
    race_unique_id: str, user: Row = Depends(auth_optional)
) -> HasVotedResponse:
    if user and user_has_voted(race_unique_id, user.id):
        return HasVotedResponse(voted=True)
    return HasVotedResponse(voted=False)


@router.get("/insight/popular-pairs")
async def _get_insight_popular_pairs() -> RaceListing:
    return RaceListing.from_service(get_popular_pairs())


@router.get("/insight/recent-races")
async def _get_insight_recent_races(user_id: None | int = None) -> RaceListing:
    return RaceListing.from_service(get_recent_races(user_id))

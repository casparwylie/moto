from fastapi import APIRouter, FastAPI

from src.racing.models import Race, RaceListing, Racer, SaveRequest
from src.racing.service import (
    get_popular_pairs,
    get_race,
    get_racer,
    get_recent_races,
    save_race,
    search_racers,
)

router = APIRouter(prefix="/api/racing")


@router.get("")
async def racer(make: str, model: str, year: str) -> Racer | None:
    if racer := get_racer(make, model, year):
        return Racer.from_db_data(racer)


@router.get("/race")
async def race(race_id: int) -> Race | None:
    race, racers = get_race(race_id)
    if race and racers:
        return Race.from_service(race, racers)


@router.get("/search")
async def search(make: str, model: str, year: str) -> list[Racer]:
    return [Racer.from_db_data(result) for result in search_racers(make, model, year)]


@router.post("/save")
async def save(request: SaveRequest) -> Race | None:
    race, racers = save_race(request.model_ids)
    if race and racers:
        return Race.from_service(race, racers)


@router.get("/insight/popular-pairs")
async def insight_popular_pairs() -> RaceListing:
    return RaceListing.from_service(get_popular_pairs())


@router.get("/insight/recent-races")
async def insight_recent_races() -> RaceListing:
    return RaceListing.from_service(get_recent_races())

from fastapi import FastAPI, APIRouter

from racing.models import Racer, SaveRequest
from racing.service import (
  get_racer,
  get_race,
  search_racers,
  save_race,
)


router = APIRouter(prefix='/api/racing')

@router.get('')
async def racer(make: str, model: str) -> Racer | None:
  if racer := get_racer(make, model):
      return Racer.from_db_data(racer)


@router.get('/race')
async def race(race_id: int) -> list[Racer]:
  return [
    Racer.from_db_data(racer)
    for racer in get_race(race_id)
  ]


@router.get('/search')
async def search(make: str, model: str) -> list[Racer]:
  return [
    Racer.from_db_data(result)
    for result in search_racers(make, model)
  ]


@router.post('/save')
async def save(request: SaveRequest) -> dict:
  race_id = save_race(request.model_ids)
  return {'race_id': race_id}

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
  make_name, racer = get_racer(make, model)
  if racer:
      return Racer.from_db_data(racer, make_name)


@router.get('/race')
async def race(race_id: int) -> list[Racer]:
  racers = get_race(race_id)
  return [
    Racer.from_db_data(racer, racer.make_name)
    for racer in get_race(race_id)
  ]


@router.get('/search')
async def search(make: str, model: str) -> list[Racer]:
  make_name, results = search_racers(make, model)
  return [
    Racer.from_db_data(result, make_name) for result in results
  ]


@router.post('/save')
async def save(request: SaveRequest) -> dict:
  race_id = save_race(request.model_ids)
  return {'race_id': race_id}

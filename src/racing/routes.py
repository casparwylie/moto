from fastapi import FastAPI, APIRouter

from racing.models import Racer
from racing.service import get_racer, search_racers


router = APIRouter(prefix='/api/racer')

@router.get('')
async def racer(make: str, model: str) -> Racer | None:
    make_name, racer = get_racer(make, model)
    if racer:
        return Racer.from_db_data(racer, make_name)


@router.get('/search')
async def search(make: str, model: str) -> list[Racer]:
    make_name, results = search_racers(make, model)
    return [
      Racer.from_db_data(result, make_name) for result in results
    ]


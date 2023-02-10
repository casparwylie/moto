from fastapi import FastAPI
import dataclasses
from fastapi.staticfiles import StaticFiles
import requests
import uvicorn
from pydantic import BaseModel
import database


app = FastAPI()
app.mount('/static', StaticFiles(directory='frontend'), name='static')

# TODO: Move to env var
M_API_KEY = 'QvIUv0aywoBXbuXNHAreHQ==t2wcm1EX72ciNWjV'
M_API_URL = 'https://api.api-ninjas.com/v1/motorcycles?model={model}&make={make}'


class Racer(BaseModel):
  full_name: str | None
  make: str | None
  model: str | None
  style: str | None
  year: str | None
  power: str | None
  torque: str | None
  weight: str | None
  weight_type: str | None

  @staticmethod
  def find_number_by_metric(value: str, metric: str) -> int:
    if value:
      return value[0:value.lower().find(metric.lower())].strip()

  @classmethod
  def from_db_data(cls, data, make_name) -> 'Racer':
    return cls(
      full_name=f'{make_name} {data.name}',
      make=make_name,
      model=data.name,
      style=data.style,
      year=data.year,
      power=data.power,
      torque=data.torque,
      weight=data.weight,
      weight_type=data.weight_type,
    )



@app.get('/api/racer')
async def racer(make: str, model: str) -> Racer | dict:

    if make and model:
      with database.engine.connect() as conn:
        make = conn.execute(
          database.build_get_make_by_name_query(make)
        ).one_or_none()
        racers = list(conn.execute(
          database.build_get_racer_by_make_model_query(make.id, model).limit(1)
        ))
      if racers:
        return Racer.from_db_data(racers[0], make.name)
    return {}


@app.get('/api/search')
async def search(make: str, model: str) -> list[Racer]:
    results = []
    if make and model:
      with database.engine.connect() as conn:
        makes = list(conn.execute(
          database.build_get_make_by_name_query(make).limit(1)
        ))
        if not makes:
          return []
        make = makes[0]
        results = list(conn.execute(
          database.build_search_racer_query(make.id, model).limit(20)
        ))
        print(len(results))
    return [
      Racer.from_db_data(result, make.name) for result in results
    ]


app.mount('/', StaticFiles(directory='frontend', html = True), name='index')


if __name__ == '__main__':
  uvicorn.run("server:app", host='0.0.0.0', reload=True, port=8000)


from fastapi import FastAPI
import dataclasses
from fastapi.staticfiles import StaticFiles
import requests
import uvicorn
from pydantic import BaseModel


app = FastAPI()
app.mount('/static', StaticFiles(directory='frontend'), name='static')

# TODO: Move to env var
M_API_KEY = 'QvIUv0aywoBXbuXNHAreHQ==t2wcm1EX72ciNWjV'
M_API_URL = 'https://api.api-ninjas.com/v1/motorcycles?model={model}&make={make}'


class Racer(BaseModel):
  full_name: str | None
  make: str | None
  model: str | None
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
  def from_api_data(cls, data: dict) -> 'Racer':
    print(data)
    weight = None
    weight_type = None
    if weight := data.get('total_weight'):
      weight_type = 'total'
    elif weight := data.get('wet_weight'):
      weight_type = 'wet'
    elif weight := data.get('dry_weight'):
      weight_type = 'dry'
    weight = cls.find_number_by_metric(weight, 'kg')
    make = data.get('make').strip()
    model = data.get('model').strip()
    return cls(
      full_name=f'{make} {model}',
      make=make,
      model=model,
      year=data.get('year').strip(),
      power=cls.find_number_by_metric(data.get('power'), 'hp'),
      torque=cls.find_number_by_metric(data.get('torque'), 'nm'),
      weight=weight,
      weight_type=weight_type,
    )

@app.get('/api/racer')
async def racer(make: str, model: str) -> Racer:

    if make and model:
      response = requests.get(
        M_API_URL.format(make=make, model=model),
        headers={'X-Api-Key': M_API_KEY},
      )
      if data := response.json():
        return Racer.from_api_data(data[0])


@app.get('/api/search')
async def search(make: str, model: str) -> list[Racer]:
    if make and model:
      response = requests.get(
        M_API_URL.format(make=make, model=model),
        headers={'X-Api-Key': M_API_KEY},
      )
      if data := response.json():
        r = [
          Racer.from_api_data(result) for result in data
        ]
        print(len(r))
        return r
    return []


app.mount('/', StaticFiles(directory='frontend', html = True), name='index')

if __name__ == '__main__':
  uvicorn.run("server:app", host='0.0.0.0', reload=True, port=8000)


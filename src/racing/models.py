from sqlalchemy import Row
from typing import Generator
from pydantic import BaseModel


class Racer(BaseModel):
  model_id: int
  name: str | None
  full_name: str | None
  make_name: str | None
  style: str | None
  year: str | None
  power: str | None
  torque: str | None
  weight: str | None
  weight_type: str | None


  @classmethod
  def from_db_data(cls, data: Row) -> 'Racer':
    return cls(
      model_id=data.id,
      full_name=f'{data.make_name} {data.name}',
      make_name=data.make_name,
      name=data.name,
      style=data.style,
      year=data.year,
      power=data.power,
      torque=data.torque,
      weight=data.weight,
      weight_type=data.weight_type,
    )


class SaveRequest(BaseModel):
  model_ids: list[int]


class Race(BaseModel):
  race_id: int
  racers: list[Racer]

  @classmethod
  def from_service(cls, race, racers) -> 'Race':
    return cls(
      race_id=race.id,
      racers=[
        Racer.from_db_data(racer_data)
        for racer_data in racers
      ]
    )


class RaceListing(BaseModel):
  races: list[Race]

  @classmethod
  def from_service(
    cls, races_and_racers: Generator[tuple, None, None]
  ) -> 'Race':
    return cls(
      races=[
        Race.from_service(*race_and_racer)
        for race_and_racer in races_and_racers
      ]
    )

from sqlalchemy import Row
from pydantic import BaseModel


class Racer(BaseModel):
  model_id: int
  full_name: str | None
  make: str | None
  model: str | None
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
      make=data.make_name,
      model=data.name,
      style=data.style,
      year=data.year,
      power=data.power,
      torque=data.torque,
      weight=data.weight,
      weight_type=data.weight_type,
    )


class SaveRequest(BaseModel):
  model_ids: list[int]


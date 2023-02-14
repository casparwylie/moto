from pydantic import BaseModel


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

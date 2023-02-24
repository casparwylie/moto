from pydantic import BaseModel

from src.racing.models import Racer


class SignUpRequest(BaseModel):
  username: str
  email: str
  password: str


class SignUpResponse(BaseModel):
  success: bool
  errors: list[str]


class LoginRequest(BaseModel):
  username: str
  password: str


class LoginResponse(BaseModel):
  success: bool


class LogoutResponse(BaseModel):
  success: bool


class AddGarageItemResponse(BaseModel):
  success: bool


class UserDataResponse(BaseModel):
  user_id: int
  username: str
  email: str

  @classmethod
  def from_db(cls, data) -> 'UserDataResponse':
    return cls(
      user_id=data.id,
      username=data.username,
      email=data.email,
    )


class GarageItem(BaseModel):
  relation: str
  name: str
  make_name: str
  year: int

  @classmethod
  def from_db(cls, data) -> 'GarageItem':
    return cls(
      relation=data.relation,
      name=data.name,
      make_name=data.make_name,
      year=data.year,
    )


class UserGarageResponse(BaseModel):
  items: list[GarageItem]

  @classmethod
  def from_db(cls, data) -> 'UserGarageResponse':
    return cls(
      items=[
        GarageItem.from_db(item)
        for item in data
      ]
    )

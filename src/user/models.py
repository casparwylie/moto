from pydantic import BaseModel
from sqlalchemy import Row

from src.racing.models import Racer


class SuccessResponse(BaseModel):
    success: bool
    errors: list[str] = []


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


class ChangePasswordRequest(BaseModel):
    old: str
    new: str


class EditUserFieldRequest(BaseModel):
    field: str
    value: str


class UserDataResponse(BaseModel):
    user_id: int
    username: str
    email: str

    @classmethod
    def from_db(cls, data: Row) -> "UserDataResponse":
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
    model_id: int | None = None

    @classmethod
    def from_db(cls, data: Row) -> "GarageItem":
        return cls(
            relation=data.relation,
            name=data.name,
            make_name=data.make_name,
            year=data.year,
            model_id=data.id,
        )


class UserGarageResponse(BaseModel):
    items: list[GarageItem]

    @classmethod
    def from_db(cls, data) -> "UserGarageResponse":
        return cls(items=[GarageItem.from_db(item) for item in data])


class DeleteGarageItemRequest(BaseModel):
    model_id: int

from pydantic import BaseModel


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


class UserDataResponse(BaseModel):
  username: str
  email: str

  @classmethod
  def from_db(cls, data) -> 'UserDataResponse':
    return cls(username=data.username, email=data.email)

from pydantic import BaseModel, Field, validator
from typing import Dict

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str

class Login(BaseModel):
    username: str
    password: str

class UserInput(BaseModel):
    year:int
    month:int
    date:int
    station:str

class UserInputName(BaseModel):
    name:str
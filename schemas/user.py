from pydantic import BaseModel, Field
from typing import Annotated

class UserCreate(BaseModel):
    number: Annotated[str, Field(min_length=1)]
    password: Annotated[str, Field(min_length=6)]

class UserLogin(BaseModel):
    number: Annotated[str, Field(min_length=1)]
    password: str

class UserInDB(BaseModel):
    id: int
    number: str
    allow_notification: bool
    role: str

class UserPublic(BaseModel):
    id: int
    number: str

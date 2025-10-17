from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    status: str = "ativo"


class UserCreate(UserBase):
    # bcrypt_sha256 supports long inputs; cap for validation and payload sanity
    password: str = Field(min_length=6, max_length=256)


class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    status: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=6, max_length=256)


class UserOut(UserBase):
    id: str
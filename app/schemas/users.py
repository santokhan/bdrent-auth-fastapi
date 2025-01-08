from typing import Optional
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    role: str
    name: str
    username: str
    phone: str
    email: Optional[EmailStr]


class UserBase(BaseModel):
    id: str
    name: str
    username: str
    verified: bool = False


class UserResponse(UserBase):
    id: int

    model_config = {"from_attributes": True}

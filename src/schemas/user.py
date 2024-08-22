import string
import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator, model_validator, root_validator
from pydantic.v1 import validator


class UserReadSchema(BaseModel):
    id: uuid.UUID
    name: str
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)


class UserDbSchema(UserReadSchema):
    role: str
    avatar: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    confirmed: bool
    is_active: bool
    model_config = ConfigDict(from_attributes=True)


class UserResponseSchema(BaseModel):
    user: UserDbSchema
    detail: str = "User successfully created."
    
class UserProfileSchema(BaseModel):
    id: UUID
    email: EmailStr
    name: str
    phone: Optional[str]
    car_number: Optional[str]

class UserCreateSchema(BaseModel):
    email: EmailStr
    name: str
    password: str
    phone: Optional[str] = None
    password_confirmation: str

    class Config:
        orm_mode = True



class UserUpdateSchema(BaseModel):
    name: Optional[str] = Field(min_length=2, max_length=50)
    email: Optional[EmailStr]


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    email: EmailStr


class ConfirmationResponse(BaseModel):
    message: str


class LogoutResponseSchema(BaseModel):
    message: str


class RequestNewPassword(BaseModel):
    new_password: str = Field(min_length=8, max_length=12)
    

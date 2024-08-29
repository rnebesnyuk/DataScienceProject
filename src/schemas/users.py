import string
import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_validator, model_validator, root_validator
from pydantic.v1 import validator


class UserReadSchema(BaseModel):
    id: uuid.UUID
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str]
    model_config = ConfigDict(from_attributes=True)


class ParkingHistorySchema(BaseModel):
    license_plate: str  
    entry_time: datetime
    exit_time: Optional[datetime]
    duration: Optional[float]  
    cost: Optional[float]  

    class Config:
        from_attributes = True


class VehicleDbSchema(BaseModel):
    license_plate: str
    brand_model: str
    is_blacklisted: bool

    class Config:
        from_attributes = True


class UserDbSchema(BaseModel):
    id: str
    email: str
    fullname: Optional[str]
    vehicles: List[VehicleDbSchema] = []
    parking_reports: List[ParkingHistorySchema] = []
    total_parking_duration: str
    total_spent_UAH: int

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=str(obj.id),
            fullname=obj.fullname,
            email=obj.email,
            vehicles=[VehicleDbSchema.from_orm(vehicle) for vehicle in obj.vehicles],
            parking_reports=[ParkingHistorySchema.from_orm(record) for record in obj.parking_reports]
        )


class UserResponseSchema(BaseModel):
    user: UserReadSchema
    detail: str = "User successfully created."


class UserCreateSchema(BaseModel):
    first_name: str = Field( max_length=50)
    last_name: str = Field( max_length=50)
    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(..., min_length=8, max_length=12)
    password_confirmation: str = Field(..., min_length=8, max_length=12)
    model_config = ConfigDict(from_attributes=True)


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


class ParkingEntryResponseSchema(BaseModel):
    license_plate: str
    detail: str
    model_config = ConfigDict(from_attributes=True)


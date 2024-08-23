from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, EmailStr

from src.models.models import Role


class UserStatusUpdate(BaseModel):
    email: EmailStr
    is_active: bool


class ImageRequest(BaseModel):
    image_id: int


class UserRoleUpdate(BaseModel):
    user_id: uuid.UUID
    role: Role


class ParkingRateCreate(BaseModel):
    rate_per_hour: int
    max_daily_rate: int
    currency: str

    class Config:
        from_attributes = True

class ParkingLotUpdate(BaseModel):
    total_spaces: int
    available_spaces: int

    class Config:
        from_attributes = True


class ParkingRateUpdate(BaseModel):
    total_spaces: int
    available_spaces: int
    occupied_spaces: Optional[int] = None  

    class Config:
        orm_mode = True


class ParkingRecordSchema(BaseModel):
    id: str
    vehicle_id: str
    entry_time: datetime
    exit_time: Optional[datetime]
    duration: Optional[int]
    cost: Optional[int]

    
class VehicleCheckSchema(BaseModel):
    license_plate: str


class ParkingRecordSchema(BaseModel):
    id: uuid.UUID
    vehicle_id: uuid.UUID
    entry_time: datetime
    exit_time: Optional[datetime] = None
    duration: Optional[int] = None
    cost: Optional[int] = None

    class Config:
        orm_mode = True
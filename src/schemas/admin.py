import uuid
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

from src.models.models import Role


class UserStatusUpdate(BaseModel):
    email: EmailStr
    is_active: bool


class UserRoleUpdate(BaseModel):
    email: EmailStr
    role: Role


class ParkingRateSpacesCreate(BaseModel):
    rate_per_hour: int
    max_daily_rate: Optional[int]
    currency: str
    total_spaces: int

    class Config:
        from_attributes = True


class ParkingRateSpacesDB(BaseModel):
    id: uuid.UUID
    rate_per_hour: int
    max_daily_rate: Optional[int]
    currency: str
    total_spaces: int

    class Config:
        from_attributes = True


class ParkingRecordSchema(BaseModel):
    id: str
    vehicle_id: str
    entry_time: datetime
    exit_time: Optional[datetime]
    duration: Optional[float]
    cost: Optional[float]


class VehicleCheckSchema(BaseModel):
    license_plate: str
    is_blacklisted: bool


class ParkingLotSchema(BaseModel):
    vehicle_id: str
    license_plate: str
    entry_time: Optional[str] = None
    is_occupied: bool

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj):
        return cls(
            vehicle_id=str(obj.vehicle_id),
            license_plate=obj.license_plate,
            entry_time=obj.entry_time.isoformat(),
            is_occupied=obj.is_occupied
        )


class ParkingRecordSchema(BaseModel):
    id: str
    vehicle_id: str
    license_plate: str
    entry_time: str
    exit_time: Optional[str] = None
    duration: Optional[int] = None
    cost: int

    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=str(obj.id),
            vehicle_id=str(obj.vehicle_id),
            license_plate=obj.license_plate,
            entry_time=obj.entry_time.isoformat(),  # Convert datetime to ISO 8601 string
            exit_time=obj.exit_time.isoformat() if obj.exit_time else None,
            duration=obj.duration,
            cost=obj.cost,
        )


class VehicleCreateSchema(BaseModel):
    license_plate: str
    brand_model: Optional[str] = Field(None, max_length=50)
    user_email: EmailStr


class VehicleSchema(BaseModel):
    id: uuid.UUID
    license_plate: str
    brand_model: Optional[str] = None
    user_email: str
    is_blacklisted: bool
    
    class Config:
        from_attributes = True
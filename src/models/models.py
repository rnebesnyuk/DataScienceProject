import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, DateTime, func, Column, Boolean, Enum, CheckConstraint, UUID, Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column, declarative_base


Base = declarative_base()


class Role(enum.Enum):
    admin: str = "admin"
    moderator: str = "moderator"
    user: str = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    email = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    password = Column(String, nullable=False)
    phone = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    vehicles = relationship("Vehicle", back_populates="user")

class BlackList(Base):
    __tablename__ = 'black_list'

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(255), unique=True, index=True)
    email = Column(String(320), unique=True, index=True, nullable=False)


class Vehicle(Base):
    __tablename__ = "vehicles"
    
    id = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    license_plate = mapped_column(String(20), unique=True, index=True, nullable=False)
    brand_model = mapped_column(String(50), index=True, unique=False, nullable=True)
    user_id = mapped_column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    is_blacklisted = mapped_column(Boolean, default=False)
    
    user = relationship("User", back_populates="vehicles")
    parking_records = relationship("ParkingRecord", back_populates="vehicle")


class ParkingRecord(Base):
    __tablename__ = "parking_records"
    
    id = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    vehicle_id = mapped_column(UUID(as_uuid=True), ForeignKey('vehicles.id'), nullable=False)
    entry_time = mapped_column(DateTime, default=func.now(), nullable=False)
    exit_time = mapped_column(DateTime, nullable=True)
    duration = mapped_column(Integer, nullable=True)
    cost = mapped_column(Integer, nullable=True)
    
    vehicle = relationship("Vehicle", back_populates="parking_records")


class ParkingRate(Base):
    __tablename__ = "parking_rates"
    
    id = mapped_column(Integer, primary_key=True, index=True)
    rate_per_hour = mapped_column(Integer, nullable=False)
    max_daily_rate = mapped_column(Integer, nullable=True)
    currency = mapped_column(String(10), default="USD", nullable=False)
    total_spaces = mapped_column(Integer, nullable=False, default=100)  
    available_spaces = mapped_column(Integer, nullable=False, default=100)  
    created_at = mapped_column(DateTime, default=func.now())
    updated_at = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class ParkingLot(Base):
    __tablename__ = "parking_lot"
    
    id = mapped_column(Integer, primary_key=True, index=True)
    total_spaces = mapped_column(Integer, nullable=False, default=100)
    available_spaces = mapped_column(Integer, nullable=False, default=100)
    created_at = mapped_column(DateTime, default=func.now())
    updated_at = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class BlackListCar(Base):
    __tablename__ = 'black_listcar'

    id = Column(Integer, primary_key=True, index=True)
    license_plate = Column(String(20), unique=True, index=True, nullable=False)
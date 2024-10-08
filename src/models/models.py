import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Integer, BigInteger, ForeignKey, DateTime, func, Column, Boolean, Enum, Float, UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column, declarative_base

Base = declarative_base()


class Role(enum.Enum):
    admin: str = "admin"
    user: str = "user"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    first_name = Column(String(20))
    last_name = Column(String(20))
    email = Column(String(length=30), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    role = Column(Enum(Role), default=Role.user, nullable=False)
    avatar = Column(String(100))
    refresh_token = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    confirmed = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True)

    vehicles = relationship("Vehicle", back_populates="user")  

    @hybrid_property
    def fullname(self):
        return self.first_name + " " + self.last_name


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
    user_email = mapped_column(String, ForeignKey('users.email'), nullable=False)
    is_blacklisted = mapped_column(Boolean, default=False)
    
    user = relationship("User", back_populates="vehicles")
    parking_records = relationship("ParkingRecord", back_populates="vehicle")
    parking_lot = relationship("ParkingLot", back_populates="vehicle", uselist=False)


class ParkingRecord(Base):
    __tablename__ = "parking_records"
    
    id = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    vehicle_id = mapped_column(UUID(as_uuid=True), ForeignKey('vehicles.id'), nullable=False)
    license_plate = mapped_column(String(20), unique=False, index=True, nullable=False)
    entry_time = mapped_column(DateTime, default=func.now(), nullable=False)
    exit_time = mapped_column(DateTime, nullable=False)
    duration = mapped_column(Float, nullable=False)
    cost = mapped_column(Float, nullable=True)
    
    vehicle = relationship("Vehicle", back_populates="parking_records")


class ParkingRates_Spaces(Base):
    __tablename__ = "parking_rates"
    
    id = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    rate_per_hour = mapped_column(Integer, nullable=False)
    max_daily_rate = mapped_column(Integer, nullable=True)
    currency = mapped_column(String(10), default="UAH", nullable=False)
    total_spaces = mapped_column(Integer, nullable=False, default=100)  
    created_at = mapped_column(DateTime, default=func.now())
    updated_at = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class ParkingLot(Base):
    __tablename__ = "parking_lot"
    
    id = mapped_column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    vehicle_id = mapped_column(UUID(as_uuid=True), ForeignKey('vehicles.id'), nullable=False)
    license_plate = mapped_column(String(20), unique=True, index=True, nullable=False)
    entry_time = mapped_column(DateTime, default=func.now(), nullable=False)
    is_occupied = mapped_column(Boolean, default=False)

    vehicle = relationship("Vehicle", back_populates="parking_lot")
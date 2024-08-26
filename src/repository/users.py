import uuid
from libgravatar import Gravatar
from datetime import datetime

from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import Depends

from src.models.models import User, Vehicle, ParkingRecord, ParkingRates_Spaces, User, Role, ParkingLot
from src.database.db import get_db
from src.schemas.users import UserCreateSchema
from src.services.cv_service import util


# User Repository
async def create_user(body: UserCreateSchema, db: AsyncSession = Depends(get_db)) -> User:
    avatar = None
    try:
        g = Gravatar(email=body.email)
        avatar = g.get_image()
    except Exception as err:
        print(err)

    new_user = User(**body.model_dump(), avatar=avatar)

    query = select(func.count(User.id))
    count = await db.execute(query)
    user_count = count.scalar()
    if user_count == 0:
        new_user.role = Role.admin

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def update_token(user: User, token: str | None, db: AsyncSession):
    user.refresh_token = token
    await db.commit()


async def get_user_by_email(email: str, db: AsyncSession = Depends(get_db)) -> User | None:
    query = select(User).filter_by(email=email)
    user = await db.execute(query)
    return user.scalar_one_or_none()


async def confirmed_email(email: str, db: AsyncSession):
    user = await get_user_by_email(email, db)
    user.confirmed = True
    user.is_active = True
    await db.commit()


async def update_password(user: User, new_password: str, db: AsyncSession) -> User:
    user.password = new_password
    await db.commit()
    await db.refresh(user)
    return user


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str):
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def create_user(self, user: User):
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user


class VehicleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_vehicle_by_license_plate(self, license_plate: str):
        result = await self.db.execute(select(Vehicle).where(Vehicle.license_plate == license_plate))
        return result.scalar_one_or_none()
    
    async def get_vehicles_by_user_email(self, email: str) -> list[Vehicle]:
        result = await self.db.execute(select(Vehicle).where(Vehicle.user_email == email))
        return result.scalars().all()

    async def create_vehicle(self, vehicle: Vehicle):
        self.db.add(vehicle)
        await self.db.commit()
        await self.db.refresh(vehicle)
        return vehicle

    async def is_vehicle_registered(self, license_plate: str) -> bool:
        vehicle = await self.get_vehicle_by_license_plate(license_plate)
        return vehicle is not None


class ParkingRecordRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_parking_records_by_vehicle_id(self, vehicle_id: int) -> list[ParkingRecord]:
        result = await self.db.execute(select(ParkingRecord).where(ParkingRecord.vehicle_id == vehicle_id))
        return result.scalars().all()

    async def create_parking_record(self, parking_record: ParkingRecord):
        self.db.add(parking_record)
        await self.db.commit()
        await self.db.refresh(parking_record)
        return parking_record

    async def get_parking_duration(self, vehicle_id: uuid.UUID) -> int | None:
        result = await self.db.execute(
            select(ParkingRecord)
            .where(ParkingRecord.vehicle_id == vehicle_id)
            .order_by(ParkingRecord.entry_time.desc())
        )
        parking_record = result.scalar_one_or_none()

        if parking_record and parking_record.exit_time:
            duration = (parking_record.exit_time - parking_record.entry_time).total_seconds() // 60
            return int(duration)
        return None
    
    async def handle_parking(self, license_plate: str):
        # Check if the vehicle is already in the parking lot
        result = await self.db.execute(
            select(ParkingLot)
            .join(Vehicle, ParkingLot.vehicle_id == Vehicle.id)
            .where(Vehicle.license_plate == license_plate)
            .order_by(ParkingLot.entry_time.desc())
        )
        parking_lot_record = result.scalar_one_or_none()

        if parking_lot_record:
            # Vehicle is in the parking lot, end the parking session
            return await self.end_parking(parking_lot_record.vehicle_id, license_plate)
        else:
            # Vehicle is not in the parking lot, start a new parking session
            return await self.add_vehicle_to_parking(license_plate)
    
    async def add_vehicle_to_parking(self, license_plate: str) -> ParkingRecord:
        # Fetch vehicle details
        vehicle_repo = VehicleRepository(self.db)
        vehicle = await vehicle_repo.get_vehicle_by_license_plate(license_plate)

        if not vehicle:
            raise ValueError("Vehicle not found.")

        # Check if vehicle is blacklisted
        if vehicle.is_blacklisted:
            raise ValueError(f"Vehicle with license plate {license_plate} is blacklisted. Go find some better place to park.")

        # Create a new parking lot entry
        parking_lot = ParkingLot(
            vehicle_id=vehicle.id,
            license_plate=license_plate,
            entry_time=datetime.now(),
            is_occupied=True
        )

        self.db.add(parking_lot)
        await self.db.commit()
        await self.db.refresh(parking_lot)

        return parking_lot
    
    async def end_parking(self, vehicle_id: uuid.UUID, license_plate: str) -> ParkingRecord:
        # Get the most recent parking lot entry for the vehicle
        result = await self.db.execute(
            select(ParkingLot)
            .where(ParkingLot.vehicle_id == vehicle_id, ParkingLot.is_occupied == True)
            .order_by(ParkingLot.entry_time.desc())
        )
        parking_lot_record = result.scalar_one_or_none()

        if not parking_lot_record:
            raise ValueError("No parking record found for this vehicle.")

        # Mark parking as ended
        exit_time = datetime.now()
        parking_lot_record.is_occupied = False

        # Calculate the parking duration and cost
        duration = (exit_time - parking_lot_record.entry_time).total_seconds() // 60
        cost = await self.calculate_cost(int(duration))

        # Move data to ParkingRecord and remove from ParkingLot
        parking_record = ParkingRecord(
            vehicle_id=vehicle_id,
            license_plate=license_plate,
            entry_time=parking_lot_record.entry_time,
            exit_time=exit_time,
            duration=duration,
            cost=cost
        )

        self.db.add(parking_record)
        await self.db.commit()
        await self.db.refresh(parking_record)
        await self.db.delete(parking_lot_record)
        await self.db.commit()

        return parking_record

    async def calculate_cost(self, duration: int) -> int:
        rate_per_hour = 20  # Example hourly rate, this should be configurable
        max_daily_rate = 100  # Example max daily rate, this should be configurable
        total_hours = (duration + 59) // 60  
        cost = total_hours * rate_per_hour
        if max_daily_rate is not None:
            cost = min(cost, max_daily_rate)
        return cost

    async def get_parking_history(self, license_plate: str) -> list[dict]:
        vehicle_query = select(Vehicle).where(Vehicle.license_plate == license_plate)
        vehicle_result = await self.db.execute(vehicle_query)
        vehicle = vehicle_result.scalar_one_or_none()
        if not vehicle:
            return []

        parking_query = select(ParkingRecord).where(ParkingRecord.vehicle_id == vehicle.id).order_by(ParkingRecord.entry_time)
        parking_result = await self.db.execute(parking_query)
        parking_records = parking_result.scalars().all()

        history = []
        for record in parking_records:
            history.append({
                "entry_time": record.entry_time,
                "exit_time": record.exit_time,
                "duration_minutes": (record.exit_time - record.entry_time).total_seconds() // 60 if record.exit_time else None,
                "cost": record.cost
            })
        return history
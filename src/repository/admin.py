import csv
import os
import uuid
from datetime import datetime

from libgravatar import Gravatar
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, func, update

from src.database.db import get_db
from src.models.models import User, Role, BlackList, Vehicle, ParkingRecord, ParkingRates_Spaces, ParkingLot
from src.schemas.users import UserCreateSchema
from src.schemas.admin import VehicleCheckSchema
from src.services.cv_service import util
from src.utils import utils



async def get_user_by_email(email: str, db: AsyncSession = Depends(get_db)) -> User | None:
    query = select(User).filter_by(email=email)
    user = await db.execute(query)
    return user.scalar_one_or_none()


async def change_user_status(user: User, is_active: bool, db: AsyncSession):
    stmt = (
        update(User)
        .where(User.id == user.id)
        .values(is_active=is_active)
        .execution_options(synchronize_session="fetch")
    )
    
    await db.execute(stmt)
    await db.commit()


async def update_user_role(user: User, role: bool, db: AsyncSession):
    stmt = (
        update(User)
        .where(User.id == user.id)
        .values(role=role)
        .execution_options(synchronize_session="fetch")
    )
    
    await db.execute(stmt)
    await db.commit()


async def generate_parking_report(license_plate: str, db: AsyncSession):
    SAVE_DIR = os.path.expanduser("~")
    os.makedirs(SAVE_DIR, exist_ok=True)

    # Query to get parking records for the found vehicle
    result = await db.execute(
        select(ParkingRecord)
        .where(ParkingRecord.license_plate == license_plate)
        .order_by(ParkingRecord.entry_time)
    )

    parking_records = result.scalars().all()

    if not parking_records:
        return None

    filename = os.path.join(SAVE_DIR, f"downloads\parking_report_{license_plate}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv")
    fields = ['Entry time', 'Exit time', 'Duration (min)', 'Cost(UAH)']
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(fields)
        for record in parking_records:
            csvwriter.writerow([record.entry_time, record.exit_time, record.duration, record.cost])

    return filename


class VehicleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_vehicle_by_license_plate(self, license_plate: str):
        license_plate = util.sanitize_license_plate(license_plate)
        result = await self.db.execute(select(Vehicle).where(Vehicle.license_plate == license_plate))
        return result.scalar_one_or_none()

    async def create_vehicle(self, vehicle: Vehicle):
        self.db.add(vehicle)
        await self.db.commit()
        await self.db.refresh(vehicle)
        return vehicle
    
    async def delete_vehicle(self, vehicle: Vehicle):

        # Ensure that any related ParkingLot and ParkingRecord entries are also deleted
        await self.db.execute(
            delete(ParkingLot).where(ParkingLot.vehicle_id == vehicle.id)
        )
        await self.db.execute(
            delete(ParkingRecord).where(ParkingRecord.vehicle_id == vehicle.id)
        )

        # Finally, delete the vehicle
        await self.db.delete(vehicle)
        await self.db.commit()
    
    async def get_all_vehicles(self,):
        # Query all vehicles
        query = select(Vehicle)
        result = await self.db.execute(query)
        vehicles = result.scalars().all()
        return vehicles
    
    async def update_blacklist_status(self, vehicle: Vehicle, is_blacklisted: bool):
        stmt = (
            update(Vehicle)
            .where(Vehicle.id == vehicle.id)
            .values(is_blacklisted=is_blacklisted)
            .execution_options(synchronize_session="fetch")
        )
        
        await self.db.execute(stmt)
        await self.db.commit()

    async def get_blacklisted_vehicles(self):
        # Query to get all blacklisted vehicles
        result = await self.db.execute(
            select(Vehicle).where(Vehicle.is_blacklisted == True)
        )
        return result.scalars().all()
    
    async def get_vehicles_in_parking_lot(self):
        # Query to get vehicles currently in the parking lot
        result = await self.db.execute(
            select(Vehicle).join(ParkingLot).where(ParkingLot.id.isnot(None))
        )
        return result.scalars().all()


class ParkingRecordRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def add_vehicle_to_parking(self, vehicle_check: VehicleCheckSchema) -> ParkingRecord:
        result = await self.db.execute(
            select(BlackList).where(BlackList.token == vehicle_check.license_plate)
        )
        blacklisted = result.scalar_one_or_none()
        if blacklisted:
            raise ValueError("Vehicle is blacklisted.")
        result = await self.db.execute(
            select(Vehicle).where(Vehicle.license_plate == vehicle_check.license_plate)
        )
        vehicle = result.scalar_one_or_none()

        if not vehicle:
            raise ValueError("Vehicle not found.")
        parking_record = ParkingRecord(
            vehicle_id=vehicle.id,
            entry_time=datetime.now()
        )

        self.db.add(parking_record)
        await self.db.commit()
        await self.db.refresh(parking_record)

        return parking_record

    async def end_parking_by_license_plate(self, license_plate: str) -> ParkingRecord:
        result = await self.db.execute(
            select(Vehicle).where(Vehicle.license_plate == license_plate)
        )
        vehicle = result.scalar_one_or_none()

        if not vehicle:
            raise ValueError("Vehicle not found.")
        result = await self.db.execute(
            select(ParkingRecord)
            .where(ParkingRecord.vehicle_id == vehicle.id)
            .order_by(ParkingRecord.entry_time.desc())
        )
        parking_record = result.scalar_one_or_none()

        if not parking_record:
            raise ValueError("No parking record found for this vehicle.")

        # Завершити паркування
        parking_record.exit_time = datetime.now()
        if parking_record.entry_time:
            duration = (parking_record.exit_time - parking_record.entry_time).total_seconds() // 60
            parking_record.duration = int(duration)
            parking_record.cost = await self.calculate_cost(parking_record.duration)

        self.db.add(parking_record)
        await self.db.commit()
        await self.db.refresh(parking_record)
        return parking_record

    async def calculate_cost(self, duration: int) -> int:
        rate_per_hour, max_daily_rate = await self.get_parking_rates()
        total_hours = (duration + 59) // 60  
        cost = total_hours * rate_per_hour
        if max_daily_rate is not None:
            cost = min(cost, max_daily_rate)

        return cost
            
    async def get_parking_records(self, vehicle_id: uuid.UUID) -> list[ParkingRecord]:
        result = await self.db.execute(
            select(ParkingRecord)
            .where(ParkingRecord.vehicle_id == vehicle_id)
            .order_by(ParkingRecord.entry_time.desc())
        )
        return result.scalars().all()

    async def get_current_parking_lot(self, vehicle_id: uuid.UUID) -> ParkingLot | None:
        result = await self.db.execute(
            select(ParkingLot)
            .where(ParkingLot.vehicle_id == vehicle_id, ParkingLot.is_occupied == True)
            .order_by(ParkingLot.entry_time.desc())
        )
        return result.scalar_one_or_none()


class ParkingLotRepository:
    def __init__(self, db: AsyncSession):
        self.db = db            

    async def set_parking_rate_spaces(self, new_rate: ParkingRates_Spaces):

        self.db.add(new_rate)
        await self.db.commit()
        await self.db.refresh(new_rate)
        return new_rate
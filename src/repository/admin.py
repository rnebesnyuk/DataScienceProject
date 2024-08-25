import csv
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.models.models import BlackListCar, User, Vehicle, ParkingRecord, ParkingRate
from fastapi import Depends
from src.database.db import get_db
from src.models.models import User, Role
from src.schemas.user import UserCreateSchema
from libgravatar import Gravatar


async def get_user_by_email(email: str, db: AsyncSession = Depends(get_db)) -> User | None:
    query = select(User).filter_by(email=email)
    user = await db.execute(query)
    return user.scalar_one_or_none()


# async def update_token(user: User, token: str | None, db: AsyncSession):
#     user.refresh_token = token
#     await db.commit()


# async def confirmed_email(email: str, db: AsyncSession):
#     user = await get_user_by_email(email, db)
#     user.confirmed = True
#     user.is_active = True
#     await db.commit()


# async def update_password(user: User, new_password: str, db: AsyncSession) -> User:
#     user.password = new_password
#     await db.commit()
#     await db.refresh(user)
#     return user


# class UserRepository:
#     def __init__(self, db: AsyncSession):
#         self.db = db

#     async def get_user_by_email(self, email: str):
#         result = await self.db.execute(select(User).where(User.email == email))
#         return result.scalar_one_or_none()

#     async def create_user(self, user: User):
#         self.db.add(user)
#         await self.db.commit()
#         await self.db.refresh(user)
#         return user


class VehicleRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_vehicle_by_license_plate(self, license_plate: str):
        result = await self.db.execute(select(Vehicle).where(Vehicle.license_plate == license_plate))
        return result.scalar_one_or_none()

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

    async def create_parking_record(self, parking_record: ParkingRecord):
        self.db.add(parking_record)
        await self.db.commit()
        await self.db.refresh(parking_record)
        return parking_record

    async def get_parking_duration(self, vehicle_id: uuid.UUID) -> int | None:
        """Повертає тривалість паркування в хвилинах для поточного паркування"""
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
    

    async def generate_parking_report(vehicle_id: uuid.UUID, db: AsyncSession):
        result = await db.execute(
            select(ParkingRecord)
            .where(ParkingRecord.vehicle_id == vehicle_id)
            .order_by(ParkingRecord.entry_time)
        )
        
        parking_records = result.scalars().all()
        
        if not parking_records:
            return None
        filename = f"parking_report_{vehicle_id}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
        fields = ['Час в’їзду', 'Час виїзду', 'Тривалість (хв)', 'Вартість (грн)']
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            csvwriter = csv.writer(csvfile)
            csvwriter.writerow(fields)
            for record in parking_records:
                csvwriter.writerow([record.entry_time, record.exit_time, record.duration, record.cost])
        
        return filename 
    

  

class BlackListRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_to_blacklist(self, license_plate: str):
        blacklisted_entry = BlackListCar(license_plate=license_plate)
        self.db.add(blacklisted_entry)
        await self.db.commit()
        return blacklisted_entry

    async def is_blacklisted(self, license_plate: str) -> bool:
        query = select(BlackListCar).where(BlackListCar.license_plate == license_plate)
        result = await self.db.execute(query)
        return result.scalar_one_or_none() is not None
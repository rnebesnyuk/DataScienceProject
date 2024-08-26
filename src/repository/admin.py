import csv
from datetime import datetime
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.schemas.admin import ParkingRateCreate
from src.models.models import BlackListCar, ParkingLot, User, Vehicle, ParkingRecord, ParkingRate

async def get_user_by_email(email: str, db: AsyncSession) -> User | None:
    query = select(User).filter_by(email=email)
    user = await db.execute(query)
    return user.scalar_one_or_none()

async def get_vehicle_by_license_plate(license_plate: str, db: AsyncSession):
    result = await db.execute(select(Vehicle).where(Vehicle.license_plate == license_plate))
    return result.scalar_one_or_none()

async def create_vehicle(vehicle: Vehicle, db: AsyncSession):
    db.add(vehicle)
    await db.commit()
    await db.refresh(vehicle)
    return vehicle

async def is_vehicle_registered(license_plate: str, db: AsyncSession) -> bool:
    vehicle = await get_vehicle_by_license_plate(license_plate, db)
    return vehicle is not None

async def create_parking_record(parking_record: ParkingRecord, db: AsyncSession):
    db.add(parking_record)
    await db.commit()
    await db.refresh(parking_record)
    return parking_record

async def get_parking_duration(vehicle_id: uuid.UUID, db: AsyncSession) -> int | None:
    """Повертає тривалість паркування в хвилинах для поточного паркування"""
    result = await db.execute(
        select(ParkingRecord)
        .where(ParkingRecord.vehicle_id == vehicle_id)
        .order_by(ParkingRecord.entry_time.desc())
    )
    parking_record = result.scalar_one_or_none()

    if parking_record and parking_record.exit_time:
        duration = (parking_record.exit_time - parking_record.entry_time).total_seconds() // 60
        return int(duration)
    return None

async def generate_parking_report(license_plate: str, db: AsyncSession) -> str:
    vehicle_result = await db.execute(
        select(Vehicle.id)
        .where(Vehicle.license_plate == license_plate)
    )
    vehicle = vehicle_result.scalar_one_or_none()
    
    if vehicle is None:
        return None

    result = await db.execute(
        select(ParkingRecord)
        .where(ParkingRecord.vehicle_id == vehicle)
        .order_by(ParkingRecord.entry_time)
    )

    parking_records = result.scalars().all()

    if not parking_records:
        return None

    # Створення імені файлу
    filename = f"parking_report_{license_plate}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
    fields = ['Entry Time', 'Exit Time', 'Duration (minutes)', 'Cost (currency)']

    # Запис в CSV
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow(fields)
        for record in parking_records:
            csvwriter.writerow([
                record.entry_time,
                record.exit_time,
                record.duration,
                record.cost
            ])

    return filename


async def save_parking_rate(
    rate_data: ParkingRateCreate,
    db: AsyncSession
) -> ParkingRate:
    new_rate = ParkingRate(
        rate_per_hour=rate_data.rate_per_hour,
        max_daily_rate=rate_data.max_daily_rate,
        currency=rate_data.currency
    )
    db.add(new_rate)
    await db.commit()
    await db.refresh(new_rate)
    return new_rate

async def get_parking_spaces(db: AsyncSession) -> ParkingLot | None:
    result = await db.execute(select(ParkingLot))
    parking_lot = result.scalars().first()
    return parking_lot

async def add_to_blacklist(license_plate: str, db: AsyncSession):
    blacklisted_entry = BlackListCar(license_plate=license_plate)
    db.add(blacklisted_entry)
    await db.commit()
    return blacklisted_entry

async def is_blacklisted(license_plate: str, db: AsyncSession) -> bool:
    query = select(BlackListCar).where(BlackListCar.license_plate == license_plate)
    result = await db.execute(query)
    return result.scalar_one_or_none() is not None
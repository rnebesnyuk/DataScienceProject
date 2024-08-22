from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.models import ParkingLot, ParkingRate, User, Role

async def change_user_status(user: User, is_active: bool, db: AsyncSession):
    user.is_active = is_active
    await db.commit()
    await db.refresh(user)

async def update_user_role(user: User, role: Role, db: AsyncSession):
    user.role = role
    await db.commit()
    await db.refresh(user)

async def set_parking_rate(rate_per_hour: int, max_daily_rate: Optional[int], currency: str, db: AsyncSession):
    new_rate = ParkingRate(
        rate_per_hour=rate_per_hour,
        max_daily_rate=max_daily_rate,
        currency=currency
    )
    db.add(new_rate)
    await db.commit()
    await db.refresh(new_rate)
    return new_rate

async def update_parking_spaces(total_spaces: int, available_spaces: int, db: AsyncSession):
    parking_lot = await db.execute(select(ParkingLot).order_by(ParkingLot.created_at.desc()))
    parking_lot = parking_lot.scalar_one_or_none()
    if parking_lot:
        parking_lot.total_spaces = total_spaces
        parking_lot.available_spaces = available_spaces
        await db.commit()
        await db.refresh(parking_lot)
        return parking_lot
    else:
        new_parking_lot = ParkingLot(
            total_spaces=total_spaces,
            available_spaces=available_spaces
        )
        db.add(new_parking_lot)
        await db.commit()
        await db.refresh(new_parking_lot)
        return new_parking_lot
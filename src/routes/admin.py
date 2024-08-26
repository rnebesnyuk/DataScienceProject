from typing import Optional
from fastapi import APIRouter, Form, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.repository import admin as repository_admin
from src.schemas.admin import ParkingLotUpdate, ParkingRateCreate, UserRoleUpdate, UserStatusUpdate, VehicleCheckSchema
from src.schemas.user import UserReadSchema
from src.models.models import User, Role
from src.services.role import RolesAccess
from src.services.auth import auth_service
from src.database.db import get_db
from src.repository import users as repository_users

router = APIRouter(prefix="/admin", tags=["admin"])

access_admin = RolesAccess([Role.admin])


@router.patch("/users/block", dependencies=[Depends(access_admin)])
async def change_user_status_by_email(
    body: UserStatusUpdate = Depends(),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(auth_service.get_current_user)
):
    user = await repository_users.get_user_by_email(body.email, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    await repository_admin.change_user_status(user, body.is_active, db)
    return {"message": f"User status changed to {'active' if body.is_active else 'banned'}."}


@router.patch("/users/unblock", dependencies=[Depends(access_admin)])
async def unblock_user_by_email(
    body: UserStatusUpdate = Depends(),
    _: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await repository_users.get_user_by_email(body.email, db)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    await repository_admin.change_user_status(user, body.is_active, db)
    return {"message": f"User status changed to {'active' if body.is_active else 'banned'}."}


@router.patch("/{user_id}/change_role", dependencies=[Depends(access_admin)])
async def update_user_role(
    body: UserRoleUpdate = Depends(),
    _: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user = await repository_users.get_user_by_id(body.user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    await repository_admin.update_user_role(user, body.role, db)
    return {"message": f"User role updated to {body.role}"}


@router.post("/parking-rates", response_model=ParkingRateCreate, dependencies=[Depends(access_admin)])
async def create_parking_rate(
    rate_data: ParkingRateCreate,
    _: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        rate = await repository_admin.save_parking_rate(
            rate_data=rate_data,
            db=db
        )
        return rate
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/parking-lot", response_model=ParkingLotUpdate, dependencies=[Depends(access_admin)])
async def update_parking_spaces(
    lot_data: ParkingLotUpdate,
    _: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    parking_lot = await repository_admin.update_parking_spaces(
        total_spaces=lot_data.total_spaces,
        available_spaces=lot_data.available_spaces,
        db=db
    )
    return parking_lot


@router.put("/parking-info", response_model=VehicleCheckSchema, dependencies=[Depends(access_admin)])
async def update_parking_info(
    lot_data: VehicleCheckSchema,  
    db: AsyncSession = Depends(get_db),
    _: User = Depends(auth_service.get_current_user),
):
    parking_info = await repository_admin.update_parking_info(
        total_spaces=lot_data.total_spaces,
        available_spaces=lot_data.available_spaces,
        rate_per_hour=lot_data.rate_per_hour,  
        max_daily_rate=lot_data.max_daily_rate,
        currency=lot_data.currency,
        db=db
    )
    return parking_info


@router.post("/add_to_blacklist", dependencies=[Depends(access_admin)])
async def add_to_blacklist(
    license_plate: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(auth_service.get_current_user),
):
    blacklist_repo = repository_admin.BlackListRepository(db)
    if await blacklist_repo.is_blacklisted(license_plate):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vehicle is already blacklisted.")
    
    blacklisted_entry = await blacklist_repo.add_to_blacklist(license_plate)
    return blacklisted_entry
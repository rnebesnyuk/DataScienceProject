from typing import Optional
from fastapi import APIRouter, Form, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.repository import admin as repository_admin
from src.schemas.admin import ParkingLotUpdate, ParkingRateCreate, ParkingRateUpdate, ParkingRecordSchema, UserRoleUpdate, UserStatusUpdate, VehicleCheckSchema, VehicleCreateSchema, VehicleReadSchema
from src.schemas.user import UserReadSchema
from src.models.models import User, Role, Vehicle
from src.services.role import RoleAccess
from src.services.auth import auth_service
from src.database.db import get_db
from src.repository import users as repository_users

router = APIRouter(prefix="/admin", tags=["admin"])
role_admin = RoleAccess([Role.admin])
role_admin_moderator = RoleAccess([Role.admin, Role.moderator])


@router.put("/users/block", dependencies=[Depends(role_admin)])
async def change_user_status_by_email(
    body: UserStatusUpdate = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user)
):
    user = await repository_users.get_user_by_email(body.email, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    await repository_admin.change_user_status(user, body.is_active, db)
    return {"message": f"User status changed to {'active' if body.is_active else 'inactive'}."}


@router.put("/unblock", dependencies=[Depends(role_admin)])
async def unblock_user_by_email(
    body: UserStatusUpdate = Depends(),
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await repository_users.get_user_by_email(body.email, db)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    await repository_admin.change_user_status(user, body.is_active, db)
    return {"message": f"User status changed to {'active' if body.is_active else 'inactive'}."}


@router.put("/{user_id}/change_role", dependencies=[Depends(role_admin)])
async def update_user_role(
    body: UserRoleUpdate = Depends(),
    db: AsyncSession = Depends(get_db)
):
    user = await repository_users.get_user_by_id(body.user_id, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    await repository_admin.update_user_role(user, body.role, db)
    return {"message": f"User role updated to {body.role}"}


@router.post("/parking-rates", response_model=ParkingRateCreate, dependencies=[Depends(role_admin)])
async def set_parking_rate(
    rate_data: ParkingRateCreate,
    db: AsyncSession = Depends(get_db)
):
    rate = await repository_admin.set_parking_rate(
        rate_per_hour=rate_data.rate_per_hour,
        max_daily_rate=rate_data.max_daily_rate,
        currency=rate_data.currency,
        db=db
    )
    return rate


@router.put("/parking-lot", response_model=ParkingLotUpdate, dependencies=[Depends(role_admin)])
async def update_parking_spaces(
    lot_data: ParkingLotUpdate,
    db: AsyncSession = Depends(get_db)
):
    parking_lot = await repository_admin.update_parking_spaces(
        total_spaces=lot_data.total_spaces,
        available_spaces=lot_data.available_spaces,
        db=db
    )
    return parking_lot


@router.put("/parking-info", response_model=ParkingRateUpdate, dependencies=[Depends(role_admin)])
async def update_parking_info(
    lot_data: ParkingRateUpdate,  
    db: AsyncSession = Depends(get_db)
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

@router.post("/add_car_to_parking", response_model=ParkingRecordSchema, dependencies=[Depends(role_admin)])
async def add_to_parking(vehicle_check: VehicleCheckSchema, db: AsyncSession = Depends(get_db)):
    vehicle_repo = repository_admin.ParkingRecordRepository(db)
    
    try:
        parking_record = await vehicle_repo.add_vehicle_to_parking(vehicle_check)
        return parking_record
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    


@router.put("/end-parking", response_model=ParkingRecordSchema, dependencies=[Depends(role_admin)])
async def end_parking(vehicle_check: VehicleCheckSchema, db: AsyncSession = Depends(get_db)):
    parking_repo = repository_admin.ParkingRecordRepository(db)
    
    try:
        parking_record = await parking_repo.end_parking_by_license_plate(vehicle_check.license_plate)
        return parking_record
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    


@router.post("/add_to_blacklist", dependencies=[Depends(role_admin)])
async def add_to_blacklist(
    license_plate: str,
    db: AsyncSession = Depends(get_db)
):
    blacklist_repo = repository_admin.BlackListRepository(db)
    if await blacklist_repo.is_blacklisted(license_plate):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Vehicle is already blacklisted.")
    
    blacklisted_entry = await blacklist_repo.add_to_blacklist(license_plate)
    return blacklisted_entry
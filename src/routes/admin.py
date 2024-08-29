from datetime import timedelta
from typing import List, Optional
import uuid
from fastapi import APIRouter, Form, HTTPException, Depends, status, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.repository import admin as repository_admin
from src.schemas.admin import ParkingRateSpacesDB, UserRoleUpdate, UserStatusUpdate, \
    ParkingRecordSchema, VehicleCheckSchema, VehicleCreateSchema, VehicleSchema, ParkingLotSchema, ParkingRateSpacesCreate
from src.schemas.users import UserReadSchema
from src.models.models import User, Role, Vehicle, ParkingRates_Spaces
from src.services.role import RolesAccess
from src.services.auth import auth_service
from src.database.db import get_db
from src.repository import users as repository_users

router = APIRouter(prefix="/admin", tags=["admin"])

access_admin = RolesAccess([Role.admin])


@router.patch("/users_status", dependencies=[Depends(access_admin)])
async def change_user_status(
    body: UserStatusUpdate = Depends(),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(auth_service.get_current_user)
):
    user = await repository_admin.get_user_by_email(body.email, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    
    await repository_admin.change_user_status(user, body.is_active, db)
    
    status = "active" if body.is_active else "banned"
    return {"message": f"User status changed to {status}."}


@router.patch("/{email}/change_role", dependencies=[Depends(access_admin)])
async def update_user_role(
    body: UserRoleUpdate = Depends(),
    _: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user = await repository_users.get_user_by_email(body.email, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    await repository_admin.update_user_role(user, body.role, db)
    return {"message": f"User role updated to {body.role}"}


@router.post("/add_vehicles", response_model=VehicleCreateSchema, dependencies=[Depends(access_admin)], status_code=status.HTTP_201_CREATED)
async def add_vehicle(
    vehicle: VehicleCreateSchema = Depends(), 
    db: AsyncSession = Depends(get_db), 
    _: User = Depends(auth_service.get_current_user)
):
    # Check if a vehicle with the same license plate already exists
    vehicle_repo = repository_admin.VehicleRepository(db)
    existing_vehicle = await vehicle_repo.get_vehicle_by_license_plate(vehicle.license_plate)
    if existing_vehicle:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vehicle with this license plate already exists."
        )
    
    # Check if the user with the provided email exists
    user = await repository_admin.get_user_by_email(vehicle.user_email, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no such user registered."
        )

    new_vehicle = Vehicle(
        license_plate=vehicle.license_plate,
        brand_model=vehicle.brand_model,
        user_email=vehicle.user_email,
    )
    
    new_vehicle = await vehicle_repo.create_vehicle(new_vehicle)

    return new_vehicle


@router.delete("/delete_vehicle/{license_plate}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(access_admin)])
async def delete_vehicle(
    license_plate: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(auth_service.get_current_user)
):
    vehicle_repo = repository_admin.VehicleRepository(db)
    
    # Get the vehicle by license plate
    vehicle = await vehicle_repo.get_vehicle_by_license_plate(license_plate)
    
    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vehicle not found."
        )
    
    # Delete the vehicle
    await vehicle_repo.delete_vehicle(vehicle)

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/vehicles/", response_model=list[VehicleSchema], dependencies=[Depends(access_admin)])
async def get_all_vehicles(db: AsyncSession = Depends(get_db), _: User = Depends(auth_service.get_current_user)):
    try:
        vehicles_repo = repository_admin.VehicleRepository(db)
        vehicles = await vehicles_repo.get_all_vehicles()
        return vehicles
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred: {str(e)}")
    

@router.get("/vehicles_in_parking", dependencies=[Depends(access_admin)], response_model=List[VehicleSchema])
async def list_vehicles_in_parking(db: AsyncSession = Depends(get_db), _: User = Depends(auth_service.get_current_user)):
    vehicle_repo = repository_admin.VehicleRepository(db)
    
    # Fetch vehicles currently in the parking lot
    vehicles_in_parking = await vehicle_repo.get_vehicles_in_parking_lot()
    
    if not vehicles_in_parking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No vehicles currently in parking.")
    
    return vehicles_in_parking
    

@router.get("/parking_records/{license_plate}", response_model=dict, dependencies=[Depends(access_admin)])
async def get_parking_records(
    license_plate: str,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(auth_service.get_current_user)
):
    vehicles_repo = repository_admin.VehicleRepository(db)
    
    vehicle = await vehicles_repo.get_vehicle_by_license_plate(license_plate)
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vehicle with license plate {license_plate} not found.")
    
    parking_repo = repository_admin.ParkingRecordRepository(db)

    parking_records = await parking_repo.get_parking_records(vehicle.id)
    if not parking_records:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "No parking records found"})
    
    current_parking_lot = await parking_repo.get_current_parking_lot(vehicle.id)

    # Calculate total duration and cost
    total_duration_minutes = sum(record.duration for record in parking_records)
    total_duration = timedelta(minutes=total_duration_minutes)
    hours, remainder = divmod(total_duration.total_seconds(), 3600)
    minutes = remainder // 60
    total_cost = sum(record.cost for record in parking_records)
    
    response = {
        "history": [ParkingRecordSchema.from_orm(record).model_dump() for record in parking_records],
        "current_parking_lot": ParkingLotSchema.from_orm(current_parking_lot).model_dump() if current_parking_lot else None,
        "total_parking_duration": f"{int(hours)} hours, {int(minutes)} minutes",
        "total_spent": f'{total_cost} UAH'
    }

    return JSONResponse(content=response)


@router.post("/parking_rates_spaces", response_model=ParkingRateSpacesDB, dependencies=[Depends(access_admin)])
async def set_parking_rate_spaces(
    rate_data: ParkingRateSpacesCreate = Depends(),
    _: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db)
):
    rates_repo = repository_admin.ParkingLotRepository(db)

    rate = ParkingRates_Spaces(
        id=uuid.uuid4(),
        rate_per_hour=rate_data.rate_per_hour,
        max_daily_rate=rate_data.max_daily_rate,
        currency=rate_data.currency,
        total_spaces=rate_data.total_spaces
    )
    
    new_rates = await rates_repo.set_parking_rate_spaces(rate)

    return new_rates


@router.get("/generate_parking_report", dependencies=[Depends(access_admin)])
async def get_parking_report(
    license_plate: str,
    db: AsyncSession = Depends(get_db), _: User = Depends(auth_service.get_current_user)
):
    vehicles_repo = repository_admin.VehicleRepository(db)
    
    vehicle = await vehicles_repo.get_vehicle_by_license_plate(license_plate)
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Vehicle with license plate {license_plate} not found.")
    
    filename = await repository_admin.generate_parking_report(license_plate, db)
    if not filename:
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": "Parking records not found for this vehicle."})
    
    return {"filename": filename}


@router.patch("/add_to_blacklist", dependencies=[Depends(access_admin)])
async def add_to_blacklist(
    body: VehicleCheckSchema = Depends(),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(auth_service.get_current_user)
):
    vehicle_repo = repository_admin.VehicleRepository(db)
    vehicle = await vehicle_repo.get_vehicle_by_license_plate(body.license_plate)
    
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found.")
    
    await vehicle_repo.update_blacklist_status(vehicle, body.is_blacklisted)

    status = "blacklisted" if body.is_blacklisted else "whitelisted"
    return {"message": f"Vehicle was {status}."}


@router.get("/blacklisted_vehicles", dependencies=[Depends(access_admin)], response_model=List[VehicleSchema])
async def list_blacklisted_vehicles(db: AsyncSession = Depends(get_db), _: User = Depends(auth_service.get_current_user)):
    vehicle_repo = repository_admin.VehicleRepository(db)
    
    # Fetch blacklisted vehicles
    blacklisted_vehicles = await vehicle_repo.get_blacklisted_vehicles()
    
    if not blacklisted_vehicles:
        raise HTTPException(status_code=404, detail="No blacklisted vehicles found.")
    
    return blacklisted_vehicles

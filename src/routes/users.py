import os
import tempfile
import uuid

from typing import List

from fastapi import APIRouter, Depends, status, HTTPException, Request, BackgroundTasks, UploadFile, File
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import HTMLResponse,JSONResponse

from src.database.db import get_db
from src.models.models import User, Vehicle
from src.repository.users import UserRepository, VehicleRepository, ParkingRecordRepository
from src.schemas.user import UserDbSchema, RequestEmail, EntryResponseSchema
from src.services.auth import auth_service
from src.services.email import send_email_reset_password
from src.services.cv_service import initiate

router = APIRouter(prefix="/users", tags=["users"])
templates = Jinja2Templates(directory="src/services/templates")


@router.get("/me/", response_model=UserDbSchema)
async def read_users_me(current_user: User = Depends(auth_service.get_current_user)):
    return current_user


@router.post("/forgot_password")
async def forgot_password(background_tasks: BackgroundTasks,
                          request: Request,
                          body: RequestEmail = Depends(),
                          db: AsyncSession = Depends(get_db)) -> dict:
    user = await UserRepository(db).get_user_by_email(body.email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user:
        background_tasks.add_task(send_email_reset_password, user.email, user.fullname, str(request.base_url))
    return {"message": "Check your email for confirmation."}


@router.post("/reset_password/{token}")
async def reset_password(token: str,
                         request_: Request,
                         db: AsyncSession = Depends(get_db)) -> dict:
    form_data = await request_.form()
    new_password = form_data["new_password"]
    email = await auth_service.get_email_from_token(token)
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    user = await UserRepository(db).get_user_by_email(email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    new_password = await auth_service.get_password_hash(new_password)
    await UserRepository(db).update_password(user, new_password, db)
    return {"message": "Password reset successfully"}


@router.get("/reset_password/{token}", response_class=HTMLResponse)
async def get_reset_password_page(token: str, request_: Request):
    return templates.TemplateResponse("reset_password.html", {"request": request_, "token": token})


@router.get("/vehicle/{license_plate}/check", response_model=dict)
async def check_vehicle_registration(license_plate: str, db: AsyncSession = Depends(get_db)):
    vehicle_repo = VehicleRepository(db)
    is_registered = await vehicle_repo.is_vehicle_registered(license_plate)
    return {"is_registered": is_registered}


@router.get("/vehicle/{vehicle_id}/parking_duration", response_model=dict)
async def get_parking_duration(vehicle_id: str, db: AsyncSession = Depends(get_db)):
    parking_repo = ParkingRecordRepository(db)
    duration = await parking_repo.get_parking_duration(uuid.UUID(vehicle_id))
    if duration is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parking record not found or still in progress")
    return {"duration_minutes": duration}


@router.post("/parking_access/", response_model=EntryResponseSchema)
async def upload_license_plate(
    file: UploadFile = File(...), db: AsyncSession = Depends(get_db)
):
    try:
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            tmp_file.write(await file.read())
            tmp_file_path = tmp_file.name

        # Pass the image to your ML model to get the license plate text
        license_plate_dict = initiate.main(tmp_file_path)
        license_plate_text = license_plate_dict[0][list(license_plate_dict[0].keys())[0]]['license_plate']['text']

        # Optionally, store the result in the database if needed
        os.remove(tmp_file_path)

        # Query the database to find the vehicle and user details
        vehicle_query = await db.execute(
            select(Vehicle).where(Vehicle.license_plate == license_plate_text).options(selectinload(Vehicle.user))
        )
        vehicle = vehicle_query.scalars().first()

        if not vehicle:
            raise HTTPException(status_code=404, detail=f"Vehicle with license_plate: {license_plate_text} not found")

        user = vehicle.user  # Assuming there's a relationship from Vehicle to User via "owner" attribute

        # Determine if the user is banned
        if not user.is_active:
            detail = "Access DENIED. Go find some better place to park!"
        else:
            detail = "Access GRANTED"            

        # Prepare response
        response = EntryResponseSchema(
            fullname=user.fullname,
            brand_model=vehicle.brand_model,
            license_plate=vehicle.license_plate,
            detail=detail
        )

        return JSONResponse(content=response.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
from datetime import timedelta
import os
import tempfile
import uuid

from typing import List

from fastapi import APIRouter, Depends, status, HTTPException, Request, BackgroundTasks, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse,JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.models.models import User, Vehicle, ParkingRecord
from src.repository import users as repository_users
from src.schemas.users import UserDbSchema, RequestEmail, ParkingEntryResponseSchema, ParkingHistorySchema, VehicleDbSchema
from src.services.auth import auth_service
from src.services.email import send_email_reset_password
from src.services.cv_service import initiate, util


router = APIRouter(prefix="/users", tags=["users"])
templates = Jinja2Templates(directory="src/services/templates")


@router.get("/me/", response_model=UserDbSchema)
async def read_users_me(current_user: User = Depends(auth_service.get_current_user), db: AsyncSession = Depends(get_db)):
    user_repo = repository_users.UserRepository(db)
    user = await user_repo.get_user_by_email(current_user.email)
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    vehicles_repo = repository_users.VehicleRepository(db)
    # Fetch vehicles associated with the user using the repository function
    vehicles = await vehicles_repo.get_vehicles_by_user_email(user.email)


    # Fetch parking records for each vehicle using the repository function
    parking_records = []
    total_duration_minutes = 0
    total_cost = 0
    record_repo = repository_users.ParkingRecordRepository(db)
    for vehicle in vehicles:
        records = await record_repo.get_parking_records_by_vehicle_id(vehicle.id)
        parking_records.extend(records)
        
        # Calculate total duration and cost
        for record in records:
            total_duration_minutes += record.duration
            total_cost += record.cost

    # Convert total duration to hours:minutes format
    total_duration = timedelta(minutes=total_duration_minutes)
    hours, remainder = divmod(total_duration.total_seconds(), 3600)
    minutes = remainder // 60
    total_parking_duration = f"{int(hours)} hours, {int(minutes)} minutes"

    # Construct the response
    user_response = UserDbSchema(
        id=str(user.id),
        fullname=user.fullname,
        email=user.email,
        vehicles=[VehicleDbSchema.from_orm(vehicle) for vehicle in vehicles],
        parking_reports=[ParkingHistorySchema.from_orm(record) for record in parking_records],
        total_parking_duration=total_parking_duration,
        total_spent_UAH=total_cost
    )

    return user_response

@router.post("/forgot_password")
async def forgot_password(background_tasks: BackgroundTasks,
                        request: Request,
                        body: RequestEmail = Depends(),
                        db: AsyncSession = Depends(get_db)) -> dict:
    user_repo = repository_users.UserRepository(db)
    user = await user_repo.get_user_by_email(body.email)
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


    user_repo = repository_users.UserRepository(db)
    user = await user_repo.get_user_by_email(email)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    new_password = await auth_service.get_password_hash(new_password)
    await repository_users.update_password(user, new_password, db)
    return {"message": "Password reset successfully"}


@router.get("/reset_password/{token}", response_class=HTMLResponse)
async def get_reset_password_page(token: str, request_: Request):
    return templates.TemplateResponse("reset_password.html", {"request": request_, "token": token})


@router.post("/parking_access/", response_model=ParkingEntryResponseSchema)
async def upload_license_plate(
    file: UploadFile = File(...), db: AsyncSession = Depends(get_db),
):
    try:
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            tmp_file.write(await file.read())
            tmp_file_path = tmp_file.name

        # Pass the image to your ML model to get the license plate text
        try:
            license_plate_dict = initiate.main(tmp_file_path)
            #license_plate_text = license_plate_dict[0][list(license_plate_dict[0].keys())[0]]['license_plate']['text']
        except Exception as e:
            response = {'detail':"Could not read the number"}
            return JSONResponse(content=response)
        finally:
            # Optionally, store the result in the database if needed
            os.remove(tmp_file_path)

        sanitized_text = util.sanitize_license_plate(license_plate_dict)

        parking_repo = repository_users.ParkingRecordRepository(db)
        try:
            parking_record = await parking_repo.handle_parking(sanitized_text)
        except ValueError as e:
            return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(e)})

        if isinstance(parking_record, ParkingRecord):
            total_duration = timedelta(minutes=parking_record.duration)
            hours, remainder = divmod(total_duration.total_seconds(), 3600)
            minutes = remainder // 60
            total_parking_duration = f"{int(hours)} hours, {int(minutes)} minutes"
            detail = f"Parking ended. Duration: {total_parking_duration}, Cost: {parking_record.cost}"
        else:
            detail = "Parking started"
        response = ParkingEntryResponseSchema(
            license_plate=sanitized_text,
            detail=detail
        )

        return JSONResponse(content=response.model_dump())
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An error occurred: {str(e)}")
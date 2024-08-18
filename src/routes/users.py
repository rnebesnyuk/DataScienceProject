from urllib import request

from fastapi import APIRouter, Depends, status, UploadFile, File, Request, BackgroundTasks, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse

from src.database.db import get_db
from src.models.models import User
from src.repository import users as repository_users
from src.services.auth import auth_service
from src.conf.config import settings
from src.schemas.user import UserDbSchema, RequestEmail, RequestNewPassword
from src.services.email import send_email_reset_password

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
    user = await repository_users.get_user_by_email(body.email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user:
        background_tasks.add_task(send_email_reset_password, user.email, user.fullname, str(request.base_url))
    return {"message": "Check your email for confirmation."}


@router.post("/reset_password/{token}")
async def reset_password(token:  str,
                         request_: Request,
                         db: AsyncSession = Depends(get_db)) -> dict:
    form_data = await request_.form()
    new_password = form_data["new_password"]
    email = await auth_service.get_email_from_token(token)
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    user = await repository_users.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    new_password = await auth_service.get_password_hash(new_password)
    await repository_users.update_password(user, new_password, db)
    return {"message": "Password reset successfully"}


@router.get("/reset_password/{token}", response_class=HTMLResponse)
async def get_reset_password_page(token: str, request_: Request):
    return templates.TemplateResponse("reset_password.html", {"request": request_, "token": token})
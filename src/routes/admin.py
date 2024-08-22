from typing import Optional
from fastapi import APIRouter, Form, HTTPException, Depends
from sqlalchemy import select

from src.repository import admin as repository_admin
from src.schemas.admin import UserRoleUpdate, UserStatusUpdate
from src.schemas.user import UserReadSchema
from src.models.models import User, Role
from src.services.role import RoleAccess
from src.services.auth import auth_service
from src.database.db import get_db
from src.repository import users as repository_users
from sqlalchemy.ext.asyncio import AsyncSession

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



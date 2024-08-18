from sqlalchemy import select
from src.models.models import User, Role, Comment
from sqlalchemy.ext.asyncio import AsyncSession


async def change_user_status(user: User, is_active: bool, db: AsyncSession):

    user.is_active = is_active
    await db.commit()
    await db.refresh(user)


async def update_user_role(user: User, role: Role, db: AsyncSession):

    user.role = role
    await db.commit()
    await db.refresh(user)
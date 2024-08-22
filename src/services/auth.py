from datetime import datetime, timedelta
from typing import Optional

from fastapi import Request

from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.conf import messages
from src.conf.config import settings
from src.database.db import get_db
from src.repository import users as repository_users

class Auth:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = settings.secret_key
    ALGORITHM = settings.algorithm
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

    async def verify_password(self, plain_password, hashed_password) -> bool:
        return self.pwd_context.verify(plain_password, hashed_password)

    async def get_password_hash(self, password) -> str:
        return self.pwd_context.hash(password)

    async def create_access_token(self, data: dict, expires_delta: Optional[float] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "access_token"})
        encoded_access_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_access_token

    async def create_refresh_token(self, data: dict, expires_delta: Optional[float] = None):
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.utcnow() + timedelta(days=30)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire, "scope": "refresh_token"})
        encoded_refresh_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_refresh_token

    async def decode_refresh_token(self, refresh_token: str):
        try:
            payload = jwt.decode(refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'refresh_token':
                email = payload['sub']
                return email
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid scope for token")
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    async def get_current_user(self, token: str, db: AsyncSession = Depends(get_db)):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload.get('scope') != 'access_token':
                raise credentials_exception
            email = payload.get("sub")
            if email is None:
                raise credentials_exception
        except JWTError:
            raise credentials_exception

        user = await repository_users.get_user_by_email(email, db)
        if user is None or not user.is_active:
            raise credentials_exception

        return user

    @staticmethod
    async def get_current_user_from_cookie(request: Request, db: AsyncSession = Depends(get_db)):
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        return await auth_service.get_current_user(token, db)

    async def create_email_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=7)
        to_encode.update({"iat": datetime.utcnow(), "exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token

    async def get_email_from_token(self, token: str):
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload["sub"]
            return email
        except JWTError as e:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid token for email verification")

    @staticmethod
    async def get_user_access_token(access_token: str = Depends(oauth2_scheme)):
        return access_token

    async def get_token_expiration_time(self, token: str):
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'access_token':
                expiration_time = datetime.utcfromtimestamp(payload['exp'])
                return expiration_time
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid scope for token")
        except JWTError:
            return

auth_service = Auth()

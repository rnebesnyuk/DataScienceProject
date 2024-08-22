from pydantic import BaseModel, EmailStr, validator
from typing import Optional
from fastapi import Form

class LoginSchema(BaseModel):
    email: EmailStr
    password: str
    
    @validator('password')
    def password_length(cls, v):
        if len(v) < 8 or len(v) > 128:
            raise ValueError('Password must be between 8 and 128 characters')
        return v
    
    @classmethod
    def as_form(
        cls,
        email: EmailStr = Form(...),
        password: str = Form(...)
    ):
        return cls(email=email, password=password)
    
class RegisterSchema(BaseModel):
    email: EmailStr
    name: str
    password: str
    password_confirmation: str
    phone: Optional[str] = None
    
    @validator('password')
    def password_length(cls, v):
        if len(v) < 8 or len(v) > 128:
            raise ValueError('Password must be between 8 and 128 characters')
        return v
    
    @classmethod
    def as_form(
        cls,
        email: EmailStr = Form(...),
        name: str = Form(...),
        password: str = Form(...),
        password_confirmation: str = Form(...),
        phone: Optional[str] = Form(None),
    ):
        return cls(email=email, name=name, password=password, password_confirmation=password_confirmation, phone=phone)
    
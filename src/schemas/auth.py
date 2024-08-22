from pydantic import BaseModel, EmailStr, validator
from typing import Optional

class LoginSchema(BaseModel):
    email: EmailStr
    password: str
    
    @validator('password')
    def password_length(cls, v):
        if len(v) < 8 or len(v) > 128:
            raise ValueError('Password must be between 8 and 128 characters')
        return v

class RegisterSchema(BaseModel):
    email: EmailStr
    name: str
    password: str
    phone: str = None
    car_number: str = None
    
    @validator('password')
    def password_length(cls, v):
        if len(v) < 8 or len(v) > 128:
            raise ValueError('Password must be between 8 and 128 characters')
        return v
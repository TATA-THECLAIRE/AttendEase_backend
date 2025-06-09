from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime
from app.models.user import UserRole, UserStatus
import uuid

# Base User Schema
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: UserRole
    phone_number: Optional[str] = None
    
    # Student specific
    student_id: Optional[str] = None
    department: Optional[str] = None
    year_of_study: Optional[int] = None
    
    # Lecturer specific
    employee_id: Optional[str] = None
    specialization: Optional[str] = None

# User Creation Schema
class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

# User Update Schema
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    department: Optional[str] = None
    year_of_study: Optional[int] = None
    specialization: Optional[str] = None
    profile_image: Optional[str] = None

# User Response Schema
class UserResponse(UserBase):
    id: uuid.UUID
    status: UserStatus
    is_email_verified: bool
    profile_image: Optional[str] = None
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Login Schemas
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

# Token Schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None

# Email Verification
class EmailVerification(BaseModel):
    email: EmailStr
    verification_code: str

# Password Reset
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v

# Face Registration
class FaceRegistration(BaseModel):
    face_encoding: str
    face_images: List[str]

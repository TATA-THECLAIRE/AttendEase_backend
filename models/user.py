from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    user_type: str

class UserCreate(UserBase):
    password: str
    matricle_number: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    level: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    user_type: str
    matricle_number: Optional[str] = None
    employee_id: Optional[str] = None
    department: Optional[str] = None
    level: Optional[str] = None
    created_at: Optional[datetime] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

def create_user_dict(user_data: UserCreate, password_hash: str) -> dict:
    """Create user dictionary for database insertion"""
    user_id = str(uuid.uuid4())
    
    user_dict = {
        "id": user_id,
        "email": user_data.email,
        "password_hash": password_hash,
        "full_name": user_data.full_name,
        "user_type": user_data.user_type,
        "matricle_number": user_data.matricle_number,
        "employee_id": user_data.employee_id,
        "department": user_data.department,
        "level": user_data.level,
        "is_active": True,
        "created_at": datetime.utcnow()
    }
    
    return user_dict

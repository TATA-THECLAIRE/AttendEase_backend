"""
Pydantic schemas for request/response models
"""

from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime, date, time
from enum import Enum

class UserType(str, Enum):
    STUDENT = "student"
    LECTURER = "lecturer"
    ADMIN = "admin"

class AttendanceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"

class SessionStatus(str, Enum):
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

# User schemas
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

class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

# Student schemas
class StudentCreate(BaseModel):
    matricule: str
    level: str
    gender: Optional[str] = None
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    guardian_name: Optional[str] = None
    guardian_phone: Optional[str] = None

class StudentResponse(StudentCreate):
    id: str
    user: UserResponse

# Course schemas
class CourseBase(BaseModel):
    code: str
    title: str
    description: Optional[str] = None
    department: str
    level: str
    credit_units: int
    semester: str

class CourseCreate(CourseBase):
    lecturer_id: Optional[str] = None

class CourseResponse(CourseBase):
    id: str
    lecturer_id: Optional[str] = None
    is_active: bool
    created_at: datetime

# Attendance schemas
class AttendanceSessionCreate(BaseModel):
    course_id: str
    session_date: date
    start_time: time
    duration_minutes: int
    location: Optional[str] = None
    description: Optional[str] = None

class AttendanceSessionResponse(BaseModel):
    id: str
    course_id: str
    lecturer_id: str
    session_date: date
    start_time: time
    end_time: time
    duration_minutes: int
    location: Optional[str] = None
    description: Optional[str] = None
    status: str
    total_enrolled: int
    total_present: int
    attendance_percentage: float
    created_at: datetime

class AttendanceRecordCreate(BaseModel):
    session_id: str
    student_id: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None

class AttendanceRecordResponse(BaseModel):
    id: str
    session_id: str
    student_id: str
    check_in_time: datetime
    status: str
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    created_at: datetime

# Dashboard schemas
class DashboardStats(BaseModel):
    total_students: int
    total_lecturers: int
    total_courses: int
    active_sessions: int
    total_checkins_today: int
    average_attendance: float

# Authentication schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse
    expires_in: int

class TokenData(BaseModel):
    user_id: str
    email: str
    user_type: UserType

from pydantic import BaseModel, validator
from typing import Optional, List
from datetime import datetime
import uuid

# Base Course Schema
class CourseBase(BaseModel):
    course_code: str
    course_name: str
    description: Optional[str] = None
    credits: int = 3
    semester: Optional[str] = None
    academic_year: Optional[str] = None
    max_students: Optional[int] = None
    
    # Geofencing
    geofence_enabled: bool = False
    geofence_latitude: Optional[str] = None
    geofence_longitude: Optional[str] = None
    geofence_radius: int = 100

# Course Creation Schema
class CourseCreate(CourseBase):
    @validator('course_code')
    def validate_course_code(cls, v):
        if len(v) < 3:
            raise ValueError('Course code must be at least 3 characters long')
        return v.upper()

# Course Update Schema
class CourseUpdate(BaseModel):
    course_name: Optional[str] = None
    description: Optional[str] = None
    credits: Optional[int] = None
    semester: Optional[str] = None
    academic_year: Optional[str] = None
    max_students: Optional[int] = None
    geofence_enabled: Optional[bool] = None
    geofence_latitude: Optional[str] = None
    geofence_longitude: Optional[str] = None
    geofence_radius: Optional[int] = None

# Course Response Schema
class CourseResponse(CourseBase):
    id: uuid.UUID
    lecturer_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Enrollment Schemas
class EnrollmentCreate(BaseModel):
    course_id: uuid.UUID

class EnrollmentResponse(BaseModel):
    id: uuid.UUID
    course_id: uuid.UUID
    student_id: uuid.UUID
    enrolled_at: datetime
    
    class Config:
        from_attributes = True

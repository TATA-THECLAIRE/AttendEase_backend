from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import selectinload
from typing import List
import logging

from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User, UserRole
from app.models.course import Course, CourseEnrollment, CourseStatus
from app.schemas.course import (
    CourseCreate, CourseUpdate, CourseResponse,
    EnrollmentCreate, EnrollmentResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)

def check_lecturer_or_admin(current_user: User):
    """Check if user is lecturer or admin"""
    if current_user.role not in [UserRole.LECTURER, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only lecturers and admins can perform this action"
        )

@router.post("/", response_model=CourseResponse)
async def create_course(
    course_data: CourseCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new course (Lecturer/Admin only)"""
    check_lecturer_or_admin(current_user)
    
    # Check if course code already exists
    result = await db.execute(select(Course).where(Course.course_code == course_data.course_code))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course code already exists"
        )
    
    new_course = Course(
        course_name=course_data.course_name,
        course_code=course_data.course_code,
        description=course_data.description,
        lecturer_id=current_user.id,
        credits=course_data.credits,
        semester=course_data.semester,
        academic_year=course_data.academic_year,
        max_students=course_data.max_students,
        geofence_enabled=course_data.geofence_enabled,
        geofence_latitude=course_data.geofence_latitude,
        geofence_longitude=course_data.geofence_longitude,
        geofence_radius=course_data.geofence_radius,
        status=CourseStatus.ACTIVE
    )
    
    db.add(new_course)
    await db.commit()
    await db.refresh(new_course)
    
    logger.info(f"Course created: {course_data.course_code} by {current_user.email}")
    
    return new_course

@router.get("/", response_model=List[CourseResponse])
async def get_courses(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get courses based on user role"""
    
    if current_user.role == UserRole.ADMIN:
        # Admin can see all courses
        result = await db.execute(
            select(Course).options(selectinload(Course.lecturer))
        )
        courses = result.scalars().all()
    
    elif current_user.role == UserRole.LECTURER:
        # Lecturer can see their own courses
        result = await db.execute(
            select(Course)
            .where(Course.lecturer_id == current_user.id)
            .options(selectinload(Course.lecturer))
        )
        courses = result.scalars().all()
    
    else:  # Student
        # Student can see enrolled courses
        result = await db.execute(
            select(Course)
            .join(CourseEnrollment)
            .where(CourseEnrollment.student_id == current_user.id)
            .options(selectinload(Course.lecturer))
        )
        courses = result.scalars().all()
    
    return courses

@router.post("/{course_id}/enroll", response_model=EnrollmentResponse)
async def enroll_student(
    course_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Enroll student in course"""
    if current_user.role != UserRole.STUDENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can enroll in courses"
        )
    
    # Check if course exists
    result = await db.execute(select(Course).where(Course.id == course_id))
    course = result.scalar_one_or_none()
    
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Course not found"
        )
    
    if course.status != CourseStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course is not active for enrollment"
        )
    
    # Check if already enrolled
    enrollment_result = await db.execute(
        select(CourseEnrollment).where(
            CourseEnrollment.course_id == course_id,
            CourseEnrollment.student_id == current_user.id
        )
    )
    if enrollment_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already enrolled in this course"
        )
    
    # Create enrollment
    new_enrollment = CourseEnrollment(
        course_id=course_id,
        student_id=current_user.id
    )
    
    db.add(new_enrollment)
    await db.commit()
    await db.refresh(new_enrollment)
    
    logger.info(f"Student enrolled: {current_user.email} in {course.course_code}")
    
    return new_enrollment

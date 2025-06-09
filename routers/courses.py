"""
Courses router for course management operations
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from database.connection import get_supabase_client
from middleware.auth_middleware import get_current_user, require_lecturer_or_admin, UserResponse

router = APIRouter()

@router.get("/", response_model=List[dict])
async def get_courses(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get courses based on user role"""
    supabase = get_supabase_client()
    
    try:
        query = supabase.table("courses").select("*")
        
        # Filter courses based on user type
        if current_user.user_type == "lecturer":
            query = query.eq("lecturer_id", current_user.id)
        elif current_user.user_type == "student":
            # Get enrolled courses for students
            enrollments = supabase.table("course_enrollments")\
                .select("course_id")\
                .eq("student_id", current_user.id)\
                .eq("status", "active")\
                .execute()
            
            course_ids = [enrollment["course_id"] for enrollment in enrollments.data]
            if course_ids:
                query = query.in_("id", course_ids)
            else:
                return []
        
        result = query.execute()
        return result.data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch courses: {str(e)}"
        )

@router.post("/")
async def create_course(
    course_data: dict,
    current_user: UserResponse = Depends(require_lecturer_or_admin)
):
    """Create a new course"""
    supabase = get_supabase_client()
    
    try:
        # Set lecturer_id if user is lecturer
        if current_user.user_type == "lecturer":
            course_data["lecturer_id"] = current_user.id
        
        result = supabase.table("courses").insert(course_data).execute()
        
        if result.data:
            return result.data[0]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create course"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create course: {str(e)}"
        )

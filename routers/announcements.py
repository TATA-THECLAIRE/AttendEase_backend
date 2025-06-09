"""
Announcements router for announcement management
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from database.connection import get_supabase_client
from middleware.auth_middleware import get_current_user, require_lecturer_or_admin, UserResponse

router = APIRouter()

@router.get("/", response_model=List[dict])
async def get_announcements(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get announcements"""
    supabase = get_supabase_client()
    
    try:
        query = supabase.table("announcements").select("*")
        
        # Filter based on user type
        if current_user.user_type == "student":
            # Students see announcements for their courses
            enrollments = supabase.table("course_enrollments")\
                .select("course_id")\
                .eq("student_id", current_user.id)\
                .eq("status", "active")\
                .execute()
            
            course_ids = [enrollment["course_id"] for enrollment in enrollments.data]
            if course_ids:
                query = query.in_("course_id", course_ids)
            else:
                return []
        elif current_user.user_type == "lecturer":
            # Lecturers see announcements for their courses
            query = query.eq("created_by", current_user.id)
        
        result = query.order("created_at", desc=True).execute()
        return result.data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch announcements: {str(e)}"
        )

@router.post("/")
async def create_announcement(
    announcement_data: dict,
    current_user: UserResponse = Depends(require_lecturer_or_admin)
):
    """Create a new announcement"""
    supabase = get_supabase_client()
    
    try:
        announcement_data["created_by"] = current_user.id
        
        result = supabase.table("announcements").insert(announcement_data).execute()
        
        if result.data:
            return result.data[0]
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create announcement"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create announcement: {str(e)}"
        )

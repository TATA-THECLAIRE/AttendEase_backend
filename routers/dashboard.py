"""
Dashboard router for dashboard statistics and data
"""

from fastapi import APIRouter, HTTPException, status, Depends
from database.connection import get_supabase_client
from middleware.auth_middleware import get_current_user, UserResponse

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats(
    current_user: UserResponse = Depends(get_current_user)
):
    """Get dashboard statistics based on user role"""
    supabase = get_supabase_client()
    
    try:
        stats = {}
        
        if current_user.user_type == "admin":
            # Admin dashboard stats
            users_count = supabase.table("users").select("*", count="exact").execute()
            students_count = supabase.table("users").select("*", count="exact").eq("user_type", "student").execute()
            lecturers_count = supabase.table("users").select("*", count="exact").eq("user_type", "lecturer").execute()
            courses_count = supabase.table("courses").select("*", count="exact").execute()
            active_sessions = supabase.table("attendance_sessions").select("*", count="exact").eq("status", "active").execute()
            
            stats = {
                "total_users": users_count.count or 0,
                "total_students": students_count.count or 0,
                "total_lecturers": lecturers_count.count or 0,
                "total_courses": courses_count.count or 0,
                "active_sessions": active_sessions.count or 0
            }
            
        elif current_user.user_type == "lecturer":
            # Lecturer dashboard stats
            courses = supabase.table("courses").select("*", count="exact").eq("lecturer_id", current_user.id).execute()
            sessions = supabase.table("attendance_sessions").select("*", count="exact").eq("lecturer_id", current_user.id).execute()
            
            stats = {
                "total_courses": courses.count or 0,
                "total_sessions": sessions.count or 0
            }
            
        elif current_user.user_type == "student":
            # Student dashboard stats
            enrollments = supabase.table("course_enrollments").select("*", count="exact").eq("student_id", current_user.id).eq("status", "active").execute()
            attendance_records = supabase.table("attendance_records").select("*", count="exact").eq("student_id", current_user.id).execute()
            
            stats = {
                "enrolled_courses": enrollments.count or 0,
                "attendance_records": attendance_records.count or 0
            }
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch dashboard stats: {str(e)}"
        )

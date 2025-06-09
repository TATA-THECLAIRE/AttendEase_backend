from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from datetime import datetime, date
from database.connection import get_supabase_client
from models.schemas import (
    AttendanceSessionCreate, AttendanceSessionResponse,
    AttendanceRecordCreate, AttendanceRecordResponse
)
from middleware.auth_middleware import get_current_user, UserResponse

router = APIRouter()
security = HTTPBearer()

@router.post("/sessions", response_model=AttendanceSessionResponse)
async def create_attendance_session(
    session_data: AttendanceSessionCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new attendance session (Lecturers and Admins only)"""
    if current_user.user_type not in ["lecturer", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only lecturers and admins can create attendance sessions"
        )
    
    supabase = get_supabase_client()
    
    try:
        # Get course enrollment count
        enrollment_result = supabase.table("course_enrollments")\
            .select("*", count="exact")\
            .eq("course_id", session_data.course_id)\
            .eq("status", "active")\
            .execute()
        
        total_enrolled = enrollment_result.count or 0
        
        # Calculate end time
        end_time = (datetime.combine(date.today(), session_data.start_time) + 
                   timedelta(minutes=session_data.duration_minutes)).time()
        
        session_record = {
            **session_data.dict(),
            "lecturer_id": current_user.id,
            "end_time": end_time.isoformat(),
            "total_enrolled": total_enrolled,
            "status": "scheduled"
        }
        
        result = supabase.table("attendance_sessions").insert(session_record).execute()
        
        if result.data:
            return AttendanceSessionResponse(**result.data[0])
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create attendance session"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create session: {str(e)}"
        )

@router.get("/sessions", response_model=List[AttendanceSessionResponse])
async def get_attendance_sessions(
    course_id: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get attendance sessions"""
    supabase = get_supabase_client()
    
    try:
        query = supabase.table("attendance_sessions").select("*")
        
        # Filter by user type
        if current_user.user_type == "lecturer":
            query = query.eq("lecturer_id", current_user.id)
        elif current_user.user_type == "student":
            # Students can only see sessions for their enrolled courses
            enrolled_courses = supabase.table("course_enrollments")\
                .select("course_id")\
                .eq("student_id", current_user.id)\
                .eq("status", "active")\
                .execute()
            
            course_ids = [enrollment["course_id"] for enrollment in enrolled_courses.data]
            if course_ids:
                query = query.in_("course_id", course_ids)
            else:
                return []
        
        # Apply filters
        if course_id:
            query = query.eq("course_id", course_id)
        if date_from:
            query = query.gte("session_date", date_from.isoformat())
        if date_to:
            query = query.lte("session_date", date_to.isoformat())
        
        query = query.order("session_date", desc=True).order("start_time", desc=True)
        result = query.execute()
        
        return [AttendanceSessionResponse(**session) for session in result.data]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch sessions: {str(e)}"
        )

@router.post("/checkin", response_model=AttendanceRecordResponse)
async def checkin_student(
    checkin_data: AttendanceRecordCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Check in a student for attendance"""
    supabase = get_supabase_client()
    
    try:
        # Verify session exists and is active
        session_result = supabase.table("attendance_sessions")\
            .select("*")\
            .eq("id", checkin_data.session_id)\
            .execute()
        
        if not session_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attendance session not found"
            )
        
        session = session_result.data[0]
        
        # Check if session is active
        if session["status"] != "active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Attendance session is not active"
            )
        
        # For students, they can only check themselves in
        if current_user.user_type == "student":
            checkin_data.student_id = current_user.id
        
        # Check if student is enrolled in the course
        enrollment_check = supabase.table("course_enrollments")\
            .select("*")\
            .eq("student_id", checkin_data.student_id)\
            .eq("course_id", session["course_id"])\
            .eq("status", "active")\
            .execute()
        
        if not enrollment_check.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Student is not enrolled in this course"
            )
        
        # Check if already checked in
        existing_record = supabase.table("attendance_records")\
            .select("*")\
            .eq("session_id", checkin_data.session_id)\
            .eq("student_id", checkin_data.student_id)\
            .execute()
        
        if existing_record.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student already checked in for this session"
            )
        
        # Determine attendance status based on time
        now = datetime.now()
        session_start = datetime.combine(
            datetime.fromisoformat(session["session_date"]).date(),
            datetime.fromisoformat(session["start_time"]).time()
        )
        
        # Get grace period from settings
        grace_period = 15  # Default 15 minutes
        
        if now <= session_start + timedelta(minutes=grace_period):
            attendance_status = "present"
        else:
            attendance_status = "late"
        
        # Create attendance record
        record_data = {
            **checkin_data.dict(),
            "check_in_time": now.isoformat(),
            "status": attendance_status
        }
        
        result = supabase.table("attendance_records").insert(record_data).execute()
        
        if result.data:
            # Update session statistics
            await update_session_stats(checkin_data.session_id)
            return AttendanceRecordResponse(**result.data[0])
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to record attendance"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Check-in failed: {str(e)}"
        )

async def update_session_stats(session_id: str):
    """Update attendance session statistics"""
    supabase = get_supabase_client()
    
    try:
        # Count present students
        present_count = supabase.table("attendance_records")\
            .select("*", count="exact")\
            .eq("session_id", session_id)\
            .in_("status", ["present", "late"])\
            .execute()
        
        # Get total enrolled
        session = supabase.table("attendance_sessions")\
            .select("total_enrolled")\
            .eq("id", session_id)\
            .execute()
        
        if session.data:
            total_enrolled = session.data[0]["total_enrolled"]
            present = present_count.count or 0
            percentage = (present / total_enrolled * 100) if total_enrolled > 0 else 0
            
            # Update session
            supabase.table("attendance_sessions")\
                .update({
                    "total_present": present,
                    "attendance_percentage": round(percentage, 2)
                })\
                .eq("id", session_id)\
                .execute()
                
    except Exception as e:
        print(f"Failed to update session stats: {str(e)}")

@router.get("/records", response_model=List[AttendanceRecordResponse])
async def get_attendance_records(
    session_id: Optional[str] = Query(None),
    student_id: Optional[str] = Query(None),
    current_user: UserResponse = Depends(get_current_user)
):
    """Get attendance records"""
    supabase = get_supabase_client()
    
    try:
        query = supabase.table("attendance_records").select("*")
        
        # Filter based on user type
        if current_user.user_type == "student":
            query = query.eq("student_id", current_user.id)
        elif current_user.user_type == "lecturer":
            # Lecturers can see records for their sessions
            lecturer_sessions = supabase.table("attendance_sessions")\
                .select("id")\
                .eq("lecturer_id", current_user.id)\
                .execute()
            
            session_ids = [session["id"] for session in lecturer_sessions.data]
            if session_ids:
                query = query.in_("session_id", session_ids)
            else:
                return []
        
        # Apply filters
        if session_id:
            query = query.eq("session_id", session_id)
        if student_id and current_user.user_type in ["lecturer", "admin"]:
            query = query.eq("student_id", student_id)
        
        query = query.order("created_at", desc=True)
        result = query.execute()
        
        return [AttendanceRecordResponse(**record) for record in result.data]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch records: {str(e)}"
        )

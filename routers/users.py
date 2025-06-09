"""
Users router for user management operations
"""

from fastapi import APIRouter, HTTPException, status, Depends, Query
from typing import List, Optional
from database.connection import get_supabase_client
from middleware.auth_middleware import get_current_user, require_admin, UserResponse

router = APIRouter()

@router.get("/", response_model=List[dict])
async def get_users(
    user_type: Optional[str] = Query(None),
    current_user: UserResponse = Depends(require_admin)
):
    """Get all users (Admin only)"""
    supabase = get_supabase_client()
    
    try:
        query = supabase.table("users").select("*")
        
        if user_type:
            query = query.eq("user_type", user_type)
        
        result = query.execute()
        return result.data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch users: {str(e)}"
        )

@router.get("/{user_id}")
async def get_user(
    user_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get user by ID"""
    supabase = get_supabase_client()
    
    # Users can only access their own data unless they're admin
    if current_user.user_type != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        result = supabase.table("users")\
            .select("*")\
            .eq("id", user_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch user: {str(e)}"
        )

@router.put("/{user_id}")
async def update_user(
    user_id: str,
    user_data: dict,
    current_user: UserResponse = Depends(get_current_user)
):
    """Update user information"""
    supabase = get_supabase_client()
    
    # Users can only update their own data unless they're admin
    if current_user.user_type != "admin" and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        # Remove sensitive fields that shouldn't be updated directly
        user_data.pop("id", None)
        user_data.pop("password_hash", None)
        user_data.pop("created_at", None)
        
        result = supabase.table("users")\
            .update(user_data)\
            .eq("id", user_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to update user: {str(e)}"
        )

@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: UserResponse = Depends(require_admin)
):
    """Delete user (Admin only)"""
    supabase = get_supabase_client()
    
    try:
        result = supabase.table("users")\
            .delete()\
            .eq("id", user_id)\
            .execute()
        
        return {"message": "User deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to delete user: {str(e)}"
        )

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
import uuid
import asyncpg

from database.connection import get_db
from auth.password import hash_password, verify_password
from auth.jwt import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_current_user
from models.user import UserCreate, UserLogin, UserResponse, TokenResponse, create_user_dict

router = APIRouter()

@router.post("/signup", response_model=TokenResponse)
async def signup(user_data: UserCreate):
    """User signup endpoint"""
    async with get_db() as conn:
        try:
            # Check if user already exists
            existing_user = await conn.fetchrow(
                "SELECT * FROM users WHERE email = $1",
                user_data.email
            )
            
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists"
                )
            
            # Hash password
            password_hash = hash_password(user_data.password)
            
            # Create user dictionary
            user_dict = create_user_dict(user_data, password_hash)
            
            # Insert user into database
            user_id = await conn.fetchval("""
                INSERT INTO users (
                    id, email, password_hash, full_name, user_type, 
                    matricle_number, employee_id, department, level, is_active
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10
                ) RETURNING id
            """, 
                user_dict["id"], 
                user_dict["email"],
                user_dict["password_hash"],
                user_dict["full_name"],
                user_dict["user_type"],
                user_dict["matricle_number"],
                user_dict["employee_id"],
                user_dict["department"],
                user_dict["level"],
                user_dict["is_active"]
            )
            
            # Create access token
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={
                    "sub": user_dict["id"],
                    "email": user_dict["email"],
                    "user_type": user_dict["user_type"]
                },
                expires_delta=access_token_expires
            )
            
            # Get created user
            user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
            
            # Return token response
            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                user=UserResponse(
                    id=user["id"],
                    email=user["email"],
                    full_name=user["full_name"],
                    user_type=user["user_type"],
                    matricle_number=user["matricle_number"],
                    employee_id=user["employee_id"],
                    department=user["department"],
                    level=user["level"],
                    created_at=user["created_at"]
                )
            )
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create user: {str(e)}"
            )

@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """User login endpoint"""
    async with get_db() as conn:
        try:
            # Find user by email
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE email = $1",
                form_data.username  # OAuth2PasswordRequestForm uses username field for email
            )
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Verify password
            if not verify_password(form_data.password, user["password_hash"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Check if user is active
            if not user["is_active"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account is deactivated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Create access token
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={
                    "sub": user["id"],
                    "email": user["email"],
                    "user_type": user["user_type"]
                },
                expires_delta=access_token_expires
            )
            
            # Return token response
            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                user=UserResponse(
                    id=user["id"],
                    email=user["email"],
                    full_name=user["full_name"],
                    user_type=user["user_type"],
                    matricle_number=user["matricle_number"],
                    employee_id=user["employee_id"],
                    department=user["department"],
                    level=user["level"],
                    created_at=user["created_at"]
                )
            )
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Login failed: {str(e)}"
            )

@router.post("/login/email", response_model=TokenResponse)
async def login_with_email(user_credentials: UserLogin):
    """User login with email endpoint"""
    async with get_db() as conn:
        try:
            # Find user by email
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE email = $1",
                user_credentials.email
            )
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # Verify password
            if not verify_password(user_credentials.password, user["password_hash"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # Check if user is active
            if not user["is_active"]:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account is deactivated"
                )
            
            # Create access token
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={
                    "sub": user["id"],
                    "email": user["email"],
                    "user_type": user["user_type"]
                },
                expires_delta=access_token_expires
            )
            
            # Return token response
            return TokenResponse(
                access_token=access_token,
                token_type="bearer",
                user=UserResponse(
                    id=user["id"],
                    email=user["email"],
                    full_name=user["full_name"],
                    user_type=user["user_type"],
                    matricle_number=user["matricle_number"],
                    employee_id=user["employee_id"],
                    department=user["department"],
                    level=user["level"],
                    created_at=user["created_at"]
                )
            )
                
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Login failed: {str(e)}"
            )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(token_data = Depends(get_current_user)):
    """Get current user information"""
    async with get_db() as conn:
        try:
            user = await conn.fetchrow(
                "SELECT * FROM users WHERE id = $1",
                token_data.user_id
            )
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            return UserResponse(
                id=user["id"],
                email=user["email"],
                full_name=user["full_name"],
                user_type=user["user_type"],
                matricle_number=user["matricle_number"],
                employee_id=user["employee_id"],
                department=user["department"],
                level=user["level"],
                created_at=user["created_at"]
            )
                
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get user info: {str(e)}"
            )

@router.get("/test")
async def test_auth():
    """Test endpoint to verify auth router is working"""
    return {"message": "Auth router is working!", "status": "success"}

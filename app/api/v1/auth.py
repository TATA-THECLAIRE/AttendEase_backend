from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timedelta, timezone
import logging
import secrets
import string

from app.core.database import get_db
from app.core.security import (
    verify_password, get_password_hash, create_access_token, 
    create_refresh_token, verify_token
)
from app.models.user import User, UserRole, UserStatus
from app.schemas.user import (
    UserCreate, UserLogin, LoginResponse, UserResponse,
    EmailVerification, PasswordResetRequest, PasswordReset,
    Token
)
from app.services.email_service import send_verification_email, send_password_reset_email

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)

# Helper functions for token generation
def generate_verification_token() -> str:
    """Generate a 6-digit verification token"""
    return ''.join(secrets.choice(string.digits) for _ in range(6))

def generate_reset_token() -> str:
    """Generate a secure reset token"""
    return secrets.token_urlsafe(32)

# Helper function to get current user
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user"""
    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    
    # Check if user already exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check for unique student_id or employee_id
    if user_data.student_id:
        result = await db.execute(select(User).where(User.student_id == user_data.student_id))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Student ID already exists"
            )
    
    if user_data.employee_id:
        result = await db.execute(select(User).where(User.employee_id == user_data.employee_id))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Employee ID already exists"
            )
    
    # Create new user
    verification_token = generate_verification_token()
    
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        phone_number=user_data.phone_number,
        student_id=user_data.student_id,
        department=user_data.department,
        year_of_study=user_data.year_of_study,
        employee_id=user_data.employee_id,
        specialization=user_data.specialization,
        email_verification_token=verification_token,
        email_verification_expires=datetime.now(timezone.utc) + timedelta(hours=24),
        status=UserStatus.PENDING
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Send verification email
    background_tasks.add_task(
        send_verification_email,
        user_data.email,
        user_data.full_name,
        verification_token
    )
    
    logger.info(f"New user registered: {user_data.email} ({user_data.role})")
    
    return new_user

@router.post("/login", response_model=LoginResponse)
async def login_user(
    user_credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """Authenticate user and return tokens"""
    
    # Find user by email
    result = await db.execute(select(User).where(User.email == user_credentials.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if user.status == UserStatus.SUSPENDED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account suspended. Contact administrator."
        )
    
    if user.status == UserStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email before logging in"
        )
    
    # Update last login
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(last_login=datetime.now(timezone.utc))
    )
    await db.commit()
    
    # Create tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}
    )
    
    logger.info(f"User logged in: {user.email}")
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user
    )

@router.post("/verify-email")
async def verify_email(
    verification_data: EmailVerification,
    db: AsyncSession = Depends(get_db)
):
    """Verify user email with verification code"""
    
    result = await db.execute(
        select(User).where(
            User.email == verification_data.email,
            User.email_verification_token == verification_data.verification_code
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code"
        )
    
    if user.email_verification_expires < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code expired"
        )
    
    # Update user status
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(
            is_email_verified=True,
            status=UserStatus.ACTIVE,
            email_verification_token=None,
            email_verification_expires=None
        )
    )
    await db.commit()
    
    logger.info(f"Email verified for user: {user.email}")
    
    return {"message": "Email verified successfully"}

@router.post("/resend-verification")
async def resend_verification(
    email: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Resend email verification code"""
    
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Generate new verification token
    verification_token = generate_verification_token()
    
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(
            email_verification_token=verification_token,
            email_verification_expires=datetime.now(timezone.utc) + timedelta(hours=24)
        )
    )
    await db.commit()
    
    # Send verification email
    background_tasks.add_task(
        send_verification_email,
        user.email,
        user.full_name,
        verification_token
    )
    
    return {"message": "Verification email sent"}

@router.post("/forgot-password")
async def forgot_password(
    request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Request password reset"""
    
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()
    
    if not user:
        # Don't reveal if email exists or not
        return {"message": "If the email exists, a reset link has been sent"}
    
    # Generate reset token
    reset_token = generate_reset_token()
    
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(
            password_reset_token=reset_token,
            password_reset_expires=datetime.now(timezone.utc) + timedelta(hours=1)
        )
    )
    await db.commit()
    
    # Send reset email
    background_tasks.add_task(
        send_password_reset_email,
        user.email,
        user.full_name,
        reset_token
    )
    
    return {"message": "If the email exists, a reset link has been sent"}

@router.post("/reset-password")
async def reset_password(
    reset_data: PasswordReset,
    db: AsyncSession = Depends(get_db)
):
    """Reset password with token"""
    
    result = await db.execute(
        select(User).where(User.password_reset_token == reset_data.token)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )
    
    if user.password_reset_expires < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token expired"
        )
    
    # Update password
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(
            hashed_password=get_password_hash(reset_data.new_password),
            password_reset_token=None,
            password_reset_expires=None
        )
    )
    await db.commit()
    
    logger.info(f"Password reset for user: {user.email}")
    
    return {"message": "Password reset successfully"}

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Get current user information"""
    return current_user

@router.post("/refresh", response_model=Token)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token"""
    
    try:
        payload = verify_token(credentials.credentials, token_type="refresh")
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Create new tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role.value}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}
    )
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )
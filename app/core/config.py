from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database - Multiple connection options
    DATABASE_URL: str  # Pooled connection (recommended for production)
    DIRECT_DATABASE_URL: Optional[str] = None  # Direct connection for migrations
    FALLBACK_DATABASE_URL: Optional[str] = None  # Fallback connection
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Redis for real-time
    REDIS_URL: str = "redis://localhost:6379"
    
    # Email (optional for now)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    
    # App
    PROJECT_NAME: str = "Student Attendance System API"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"

settings = Settings()

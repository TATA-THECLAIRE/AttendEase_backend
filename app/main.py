from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import all models to ensure they're registered with SQLAlchemy
from app.models.user import User
from app.models.course import Course, CourseEnrollment
from app.models.session import Session
from app.models.attendance import AttendanceRecord, AttendanceSession

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("🚀 Starting Student Attendance System API...")
    
    try:
        # Initialize database
        from app.core.database import init_db
        await init_db()
        logger.info("✅ Database initialized successfully!")
        logger.info("✅ Application started successfully with database!")
        
    except Exception as e:
        logger.error(f"⚠️ Application started in limited mode: {e}")
    
    yield
    
    logger.info("🔄 Shutting down Student Attendance System API...")

# Create FastAPI app
app = FastAPI(
    title="Student Attendance System API",
    description="A comprehensive API for managing student attendance with real-time features",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include routers
from app.api.v1 import auth, courses

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(courses.router, prefix="/api/v1/courses", tags=["Courses"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "🎓 Student Attendance System API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "API is running"}

@app.get("/api/v1/test")
async def test_endpoint():
    """Test endpoint"""
    return {"message": "API is working!", "timestamp": "2025-06-09"}

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
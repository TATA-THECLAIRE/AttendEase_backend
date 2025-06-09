from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import enum

class SessionStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class Session(Base):
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Course relationship
    course_id = Column(UUID(as_uuid=True), ForeignKey('courses.id'), nullable=False)
    course = relationship("Course", back_populates="sessions")
    
    # Session details
    session_name = Column(String(255), nullable=False)
    session_type = Column(String(50), default="lecture")  # lecture, lab, tutorial
    description = Column(Text, nullable=True)
    
    # Timing
    scheduled_start = Column(DateTime(timezone=True), nullable=False)
    scheduled_end = Column(DateTime(timezone=True), nullable=False)
    actual_start = Column(DateTime(timezone=True), nullable=True)
    actual_end = Column(DateTime(timezone=True), nullable=True)
    
    # Status
    status = Column(Enum(SessionStatus), default=SessionStatus.SCHEDULED)
    
    # Attendance settings
    attendance_window_minutes = Column(Integer, default=15)  # How long students can check in
    require_geofence = Column(Boolean, default=True)
    require_face_recognition = Column(Boolean, default=True)
    
    # Location (can override course location)
    latitude = Column(String(50), nullable=True)
    longitude = Column(String(50), nullable=True)
    location_name = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    attendance_records = relationship("AttendanceRecord", back_populates="session", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Session {self.session_name} - {self.course.course_code}>"

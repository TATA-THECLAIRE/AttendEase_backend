from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text, Enum, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import enum

class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"

class CheckInMethod(str, enum.Enum):
    FACE_RECOGNITION = "face_recognition"
    MANUAL = "manual"
    QR_CODE = "qr_code"
    GEOLOCATION = "geolocation"

class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.id'), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Attendance details
    status = Column(Enum(AttendanceStatus), default=AttendanceStatus.ABSENT)
    check_in_method = Column(Enum(CheckInMethod), default=CheckInMethod.FACE_RECOGNITION)
    check_in_time = Column(DateTime(timezone=True), nullable=True)
    
    # Location verification
    latitude = Column(String(50), nullable=True)
    longitude = Column(String(50), nullable=True)
    location_verified = Column(Boolean, default=False)
    
    # Face recognition verification
    face_verified = Column(Boolean, default=False)
    face_confidence = Column(Float, nullable=True)
    
    # Additional info
    notes = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    session = relationship("Session", back_populates="attendance_records")
    student = relationship("User")
    
    def __repr__(self):
        return f"<AttendanceRecord {self.student_id} - {self.session_id}: {self.status}>"

class AttendanceSession(Base):
    __tablename__ = "attendance_sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.id'), nullable=False)
    
    # Session control
    is_active = Column(Boolean, default=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Settings
    auto_close_minutes = Column(Integer, default=15)
    require_geofence = Column(Boolean, default=True)
    require_face_recognition = Column(Boolean, default=True)
    
    # Statistics
    total_students = Column(Integer, default=0)
    present_count = Column(Integer, default=0)
    absent_count = Column(Integer, default=0)
    late_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    session = relationship("Session")
    
    def __repr__(self):
        return f"<AttendanceSession {self.session_id}: {'Active' if self.is_active else 'Inactive'}>"

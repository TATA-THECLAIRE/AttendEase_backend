from sqlalchemy import Column, String, Text, DateTime, Boolean, Integer, ForeignKey, Table, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
import uuid
import enum

class CourseStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"

# Association table for course enrollments
course_enrollments = Table(
    'course_enrollments',
    Base.metadata,
    Column('course_id', UUID(as_uuid=True), ForeignKey('courses.id'), primary_key=True),
    Column('student_id', UUID(as_uuid=True), ForeignKey('users.id'), primary_key=True),
    Column('enrolled_at', DateTime(timezone=True), server_default=func.now())
)

class Course(Base):
    __tablename__ = "courses"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_code = Column(String(20), unique=True, nullable=False)
    course_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    credits = Column(Integer, default=3)
    
    # Lecturer
    lecturer_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Course settings
    status = Column(Enum(CourseStatus), default=CourseStatus.ACTIVE)
    semester = Column(String(50), nullable=True)
    academic_year = Column(String(20), nullable=True)
    max_students = Column(Integer, nullable=True)
    
    # Geofencing
    geofence_enabled = Column(Boolean, default=False)
    geofence_latitude = Column(String(50), nullable=True)
    geofence_longitude = Column(String(50), nullable=True)
    geofence_radius = Column(Integer, default=100)  # meters
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    lecturer = relationship("User", foreign_keys=[lecturer_id])
    students = relationship("User", secondary=course_enrollments, backref="enrolled_courses")
    sessions = relationship("Session", back_populates="course", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Course {self.course_code}: {self.course_name}>"

class CourseEnrollment(Base):
    __tablename__ = "course_enrollments_detailed"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    course_id = Column(UUID(as_uuid=True), ForeignKey('courses.id'), nullable=False)
    student_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    enrolled_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    course = relationship("Course")
    student = relationship("User")
    
    def __repr__(self):
        return f"<CourseEnrollment {self.student_id} -> {self.course_id}>"

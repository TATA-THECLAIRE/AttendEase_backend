import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, Base
from app.models.user import User
from app.models.course import Course, CourseEnrollment
from app.models.session import Session
from app.models.attendance import AttendanceRecord, AttendanceSession

async def create_tables():
    """Create all database tables"""
    print("🔄 Creating database tables...")
    
    try:
        async with engine.begin() as conn:
            # Drop all tables first (be careful in production!)
            print("⚠️ Dropping existing tables...")
            await conn.run_sync(Base.metadata.drop_all)
            
            # Create all tables
            print("✅ Creating new tables...")
            await conn.run_sync(Base.metadata.create_all)
            
        print("🎉 All tables created successfully!")
        
        # Print table information
        print("\n📋 Created tables:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
    
    return True

async def main():
    """Main function"""
    print("🚀 Database Table Creation Script")
    print("=" * 50)
    
    success = await create_tables()
    
    if success:
        print("\n✅ Database setup completed successfully!")
        print("You can now start your FastAPI server.")
    else:
        print("\n❌ Database setup failed!")
        print("Please check your database connection and try again.")

if __name__ == "__main__":
    asyncio.run(main())

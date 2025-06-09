import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.pool import StaticPool, NullPool
import asyncpg

logger = logging.getLogger(__name__)

# Database configuration - Updated with your Supabase connection
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres.mjdoekgsacubsdkuuopz:08200108dyekrane@aws-0-eu-west-1.pooler.supabase.com:6543/postgres"
)

# Convert to async URL for SQLAlchemy async
ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

# Create async engine
async_engine = None
AsyncSessionLocal = None
Base = declarative_base()

def create_database_engine():
    """Create async database engine with proper configuration for Supabase"""
    global async_engine, AsyncSessionLocal
    
    try:
        # Option 1: Use default async pooling (recommended for production)
        # For async engines, SQLAlchemy automatically uses AsyncAdaptedQueuePool
        async_engine = create_async_engine(
            ASYNC_DATABASE_URL,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=300,  # Recycle connections every 5 minutes
            connect_args={
                "statement_cache_size": 0,
                "prepared_statement_cache_size": 0,
                "command_timeout": 60,
                "server_settings": {
                    "application_name": "student_attendance_api"
                }
            },
            echo=False,
        )
        
        # Alternative Option 2: Use StaticPool (single connection)
        # async_engine = create_async_engine(
        #     ASYNC_DATABASE_URL,
        #     poolclass=StaticPool,
        #     pool_pre_ping=True,
        #     connect_args={
        #         "statement_cache_size": 0,
        #         "prepared_statement_cache_size": 0,
        #         "command_timeout": 60,
        #         "server_settings": {
        #             "application_name": "student_attendance_api"
        #         }
        #     },
        #     echo=False,
        # )
        
        # Alternative Option 3: Use NullPool (no connection pooling)
        # async_engine = create_async_engine(
        #     ASYNC_DATABASE_URL,
        #     poolclass=NullPool,
        #     pool_pre_ping=True,
        #     connect_args={
        #         "statement_cache_size": 0,
        #         "prepared_statement_cache_size": 0,
        #         "command_timeout": 60,
        #         "server_settings": {
        #             "application_name": "student_attendance_api"
        #         }
        #     },
        #     echo=False,
        # )
        
        # Use async_sessionmaker
        AsyncSessionLocal = async_sessionmaker(
            bind=async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info("✅ Async database engine created successfully for Supabase")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create database engine: {e}")
        logger.error(f"Full error details: {type(e).__name__}: {str(e)}")
        return False

async def test_database_connection():
    """Test async database connection with better error handling"""
    if not async_engine:
        logger.error("❌ No async engine available")
        return False
        
    try:
        # Test with a simple query and timeout
        async with async_engine.begin() as connection:
            result = await connection.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            logger.info(f"✅ Database connection test successful: {row}")
            return True
    except asyncpg.exceptions.DuplicatePreparedStatementError as e:
        logger.error(f"❌ Prepared statement error (Supabase/pgbouncer issue): {e}")
        return False
    except OperationalError as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected database error: {type(e).__name__}: {e}")
        return False

async def init_db():
    """Initialize database"""
    logger.info("🔄 Initializing database...")
    
    # Create engine
    if not create_database_engine():
        raise Exception("Failed to create database engine")
    
    # Test connection
    if not await test_database_connection():
        logger.warning("⚠️ Database connection test failed, but continuing...")
        # Don't raise exception here - let the app start in limited mode
        return False
    
    try:
        # Create tables
        async with async_engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created/verified")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        raise

async def get_db():
    """Get async database session"""
    if not AsyncSessionLocal:
        raise Exception("Database not initialized")
        
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Health check function
async def get_database_status():
    """Get database connection status"""
    if not async_engine:
        return {"status": "disconnected", "message": "Database engine not created"}
    
    try:
        async with async_engine.begin() as connection:
            await connection.execute(text("SELECT 1"))
        return {"status": "connected", "message": "Database connection healthy"}
    except Exception as e:
        return {"status": "error", "message": f"Database connection error: {str(e)}"}

# Manual connection test function for debugging
async def debug_asyncpg_connection():
    """Debug function to test direct asyncpg connection"""
    try:
        # Extract connection details from URL
        import re
        match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
        if not match:
            logger.error("Could not parse database URL")
            return False
            
        user, password, host, port, database = match.groups()
        
        # Try direct asyncpg connection
        conn = await asyncpg.connect(
            user=user,
            password=password,
            host=host,
            port=int(port),
            database=database,
            statement_cache_size=0,
            prepared_statement_cache_size=0,
            command_timeout=60
        )
        
        result = await conn.fetchval("SELECT 1")
        await conn.close()
        
        logger.info(f"✅ Direct asyncpg connection successful: {result}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Direct asyncpg connection failed: {e}")
        return False
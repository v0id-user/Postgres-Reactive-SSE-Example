"""Database configuration and session management."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Database configuration
POSTGRESQL_URL = os.getenv("POSTGRESQL_URL", "postgresql://root:root@localhost:5432/dum_db")
engine = create_engine(POSTGRESQL_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database dependency
def get_db():
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_db_connection():
    """Get asyncpg connection for real-time notifications."""
    import asyncpg
    return await asyncpg.connect(POSTGRESQL_URL)

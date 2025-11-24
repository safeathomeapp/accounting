"""
Module: database
Purpose: Database connection and session management
Dependencies: SQLAlchemy, psycopg2
Platform: Platform-agnostic

This module handles:
- Database connection creation
- Session management
- Connection pooling

Example:
    from backend.database import SessionLocal, engine

    db = SessionLocal()
    result = db.query(Transaction).all()

Author: Claude Code
Created: November 23, 2025
Last Modified: November 23, 2025
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import os

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/accountancy_dev"
)

# Create engine
# NullPool is used for development to avoid connection pooling issues
# In production, use QueuePool with appropriate pool_size and max_overflow
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    pool_pre_ping=True,  # Verify connections before using them
    poolclass=NullPool if "localhost" in DATABASE_URL else None
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Session:
    """
    Dependency for FastAPI to get database session.

    Yields a database session, ensuring it's closed after use.

    Yields:
        Session: SQLAlchemy session

    Example:
        @app.get("/contacts")
        def get_contacts(db: Session = Depends(get_db)):
            return db.query(Client).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

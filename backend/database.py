"""
Module: database
Purpose: Database connection and session management
Dependencies: SQLAlchemy, psycopg2
Platform: Platform-agnostic

This module handles:
- Database connection creation
- Session management
- Connection pooling
- Row-Level Security (RLS) tenant context management

Example:
    from backend.database import SessionLocal, engine

    db = SessionLocal()
    result = db.query(Transaction).all()

RLS Usage:
    # Set tenant context before querying tenant-scoped tables
    from backend.database import set_tenant_context
    set_tenant_context(db, organization_id)

Author: Claude Code
Created: November 23, 2025
Last Modified: February 2, 2026
"""

from typing import Generator, Optional
from uuid import UUID
import logging

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import os

logger = logging.getLogger(__name__)

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


def set_tenant_context(db: Session, organization_id: Optional[UUID]) -> None:
    """
    Set the Row-Level Security (RLS) tenant context for the current session.

    This MUST be called after authentication and before querying any
    tenant-scoped tables. Without this, RLS policies will block all rows.

    Args:
        db: SQLAlchemy database session
        organization_id: The organization UUID to set as the tenant context.
                        If None, clears the context (no rows will be visible).

    Example:
        user = get_current_user(...)
        set_tenant_context(db, user.organization_id)
        # Now queries will only return rows for this organization
    """
    if organization_id is not None:
        # Set the session variable that RLS policies check
        db.execute(text("SET app.org_id = :org_id"), {"org_id": str(organization_id)})
        logger.debug(f"RLS tenant context set to organization: {organization_id}")
    else:
        # Reset/clear the context - queries will return no rows
        db.execute(text("RESET app.org_id"))
        logger.debug("RLS tenant context cleared")


def clear_tenant_context(db: Session) -> None:
    """
    Clear the Row-Level Security (RLS) tenant context.

    After clearing, queries to tenant-scoped tables will return no rows
    (default-deny behavior).

    Args:
        db: SQLAlchemy database session
    """
    db.execute(text("RESET app.org_id"))
    logger.debug("RLS tenant context cleared")


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to get database session.

    Yields a database session, ensuring it's closed after use.

    NOTE: This does NOT set RLS tenant context. For authenticated routes
    that access tenant data, you MUST call set_tenant_context() after
    authentication or use get_db_with_rls() instead.

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


def get_db_with_tenant(organization_id: UUID) -> Generator[Session, None, None]:
    """
    Get a database session with RLS tenant context already set.

    This is useful for background jobs or scripts that need to operate
    on a specific tenant's data.

    Args:
        organization_id: The organization UUID to set as tenant context

    Yields:
        Session: SQLAlchemy session with RLS context set

    Example:
        for db in get_db_with_tenant(org_id):
            clients = db.query(Client).all()  # Only this org's clients
    """
    db = SessionLocal()
    try:
        set_tenant_context(db, organization_id)
        yield db
    finally:
        db.close()

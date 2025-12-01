"""Database session management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from inventory_app.config import DB_URL

# Create engine
engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False},  # Needed for SQLite with threads
    echo=False  # Set to True for SQL debugging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    """Get a database session (non-generator version for use in services)."""
    return SessionLocal()


def init_db():
    """Initialize the database by creating all tables if they don't exist.

    This ensures core tables (e.g., `users`) exist for first-run scenarios
    without requiring Alembic migrations to be executed manually.
    """
    # Import models to ensure tables are registered on Base.metadata
    try:
        from inventory_app.models import user, product, order, customer, stock, audit, payment  # noqa: F401
    except Exception:
        # Even if some optional models fail to import, proceed to create known ones
        pass
    Base.metadata.create_all(bind=engine)


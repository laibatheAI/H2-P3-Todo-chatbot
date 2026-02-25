from sqlmodel import create_engine, Session
from typing import Generator
from contextlib import contextmanager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./todo_app.db")

# If using SQLite with relative path, convert to absolute path to ensure consistency
if DATABASE_URL.startswith("sqlite:///./"):
    # Get the directory of this file and create absolute path
    import pathlib
    current_dir = pathlib.Path(__file__).parent.parent.parent.absolute()  # Go up to project root
    db_filename = DATABASE_URL[10:]  # Remove "sqlite:///./" prefix
    abs_db_path = current_dir / db_filename
    DATABASE_URL = f"sqlite:///{abs_db_path}"

# Determine if we're using SQLite (for local development) or PostgreSQL
if DATABASE_URL.startswith("sqlite"):
    # SQLite engine configuration
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # Required for SQLite
        echo=False  # Set to True for debugging SQL queries
    )
else:
    # PostgreSQL engine configuration for production
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,  # Recycle connections every 5 minutes
        pool_size=10,     # Increase pool size for concurrent requests
        max_overflow=20,  # Allow additional connections when needed
        connect_args={
            "sslmode": "require",  # Require SSL for Neon
            "connect_timeout": 10, # Set connection timeout to 10 seconds
        }
    )

def get_session() -> Generator[Session, None, None]:
    """
    Get a database session for dependency injection in FastAPI.
    """
    with Session(engine) as session:
        yield session

# Export DATABASE_URL and engine for other modules to import
__all__ = ["engine", "get_session", "DATABASE_URL"]



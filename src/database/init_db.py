from sqlmodel import SQLModel, create_engine
from .database import DATABASE_URL, engine
from ..models.user import User
from ..models.task import Task

def create_db_and_tables():
    """
    Create database tables based on SQLModel models.
    This function should be called on application startup.
    """
    # Use the same engine instance from database.py to ensure consistency
    SQLModel.metadata.create_all(engine)
    print("Database tables created successfully!")
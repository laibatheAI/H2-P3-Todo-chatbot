"""
Script to initialize the database tables.
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.src.database.database import engine
from backend.src.models.task import Task
from backend.src.models.user import User
from sqlmodel import SQLModel

def create_tables():
    """Create all database tables."""
    print("Creating database tables...")
    # Make sure all models are imported before creating tables
    _ = Task, User  # Reference the models to ensure they're loaded
    SQLModel.metadata.create_all(engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    create_tables()
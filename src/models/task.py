from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import uuid

class TaskBase(SQLModel):
    title: str = Field(min_length=2, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)
    completed: bool = Field(default=False)
    priority: str = Field(default="medium")  # low, medium, high, urgent
    category: str = Field(default="other")  # work, personal, shopping, health, education, other
    due_date: Optional[datetime] = Field(default=None)
    user_id: str = Field(foreign_key="user.id")  # Match User model's id type (str)

class Task(TaskBase, table=True):
    """
    Task model representing a user's task with title, description, completion status,
    creation timestamp, and association to a specific user.
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)  # Match User model's id type
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
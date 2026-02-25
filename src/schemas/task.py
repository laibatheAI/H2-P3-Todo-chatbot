"""
Schema definitions for the Task API.
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class TaskPriority(str, Enum):
    """Task priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskCategory(str, Enum):
    """Task categories for organization."""
    WORK = "work"
    PERSONAL = "personal"
    SHOPPING = "shopping"
    HEALTH = "health"
    EDUCATION = "education"
    OTHER = "other"


# ============ Request Schemas ============

class TaskCreate(BaseModel):
    """Schema for creating a new task."""
    title: str = Field(..., min_length=2, max_length=100, description="Task title")
    description: Optional[str] = Field(default=None, max_length=1000, description="Task description")
    priority: TaskPriority = Field(default=TaskPriority.MEDIUM, description="Task priority level")
    category: Optional[TaskCategory] = Field(default=TaskCategory.OTHER, description="Task category")
    due_date: Optional[datetime] = Field(default=None, description="Task due date")
    completed: bool = Field(default=False, description="Task completion status")


class TaskUpdate(BaseModel):
    """Schema for updating an existing task."""
    title: Optional[str] = Field(default=None, min_length=2, max_length=100, description="Task title")
    description: Optional[str] = Field(default=None, max_length=1000, description="Task description")
    priority: Optional[TaskPriority] = Field(default=None, description="Task priority level")
    category: Optional[TaskCategory] = Field(default=None, description="Task category")
    due_date: Optional[datetime] = Field(default=None, description="Task due date")
    completed: Optional[bool] = Field(default=None, description="Task completion status")


# ============ Response Schemas ============

class TaskResponse(BaseModel):
    """Schema for task response."""
    id: str = Field(..., description="Unique task identifier")
    user_id: str = Field(..., description="ID of the user who owns this task")
    title: str = Field(..., description="Task title")
    description: Optional[str] = Field(default=None, description="Task description")
    priority: TaskPriority = Field(..., description="Task priority level")
    category: TaskCategory = Field(..., description="Task category")
    due_date: Optional[datetime] = Field(default=None, description="Task due date")
    completed: bool = Field(..., description="Task completion status")
    created_at: datetime = Field(..., description="Task creation timestamp")
    updated_at: datetime = Field(..., description="Task last update timestamp")

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Schema for listing multiple tasks."""
    tasks: list[TaskResponse] = Field(..., description="List of tasks")
    total_count: int = Field(..., description="Total number of tasks")
    page: int = Field(default=1, description="Current page number")
    page_size: int = Field(default=10, description="Number of tasks per page")


class MessageResponse(BaseModel):
    """Schema for simple message responses."""
    message: str = Field(..., description="Response message")
    success: bool = Field(default=True, description="Whether the operation was successful")

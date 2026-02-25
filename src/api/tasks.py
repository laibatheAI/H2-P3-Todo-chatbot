"""
Task API routes for CRUD operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from typing import Optional
from datetime import datetime
from uuid import uuid4

from src.database.database import get_session
from src.models.user import User
from src.models.task import Task
from src.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    MessageResponse,
    TaskPriority,
    TaskCategory,
)
from src.services.jwt_service import verify_token, get_user_id_from_token
from fastapi import Header


router = APIRouter(prefix="/api/tasks", tags=["Tasks"])


# ============ Authentication Dependency ============

def get_current_user_id(authorization: str = Header(None)) -> str:
    """
    Dependency to get the current user ID from JWT token.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = authorization[7:]  # Remove "Bearer " prefix
    payload = verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


# ============ CRUD Operations ============

@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_data: TaskCreate,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    """
    Create a new task for the authenticated user.
    """
    # Create task instance
    task = Task(
        id=str(uuid4()),
        user_id=user_id,
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority.value,
        category=task_data.category.value if task_data.category else TaskCategory.OTHER.value,
        due_date=task_data.due_date,
        completed=task_data.completed,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    session.add(task)
    session.commit()
    session.refresh(task)
    
    return task


@router.get("", response_model=TaskListResponse)
def get_tasks(
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
    completed: Optional[bool] = Query(None, description="Filter by completion status"),
    priority: Optional[TaskPriority] = Query(None, description="Filter by priority"),
    category: Optional[TaskCategory] = Query(None, description="Filter by category"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
):
    """
    Get all tasks for the authenticated user with optional filtering and pagination.
    """
    # Build query
    statement = select(Task).where(Task.user_id == user_id)
    
    # Apply filters
    if completed is not None:
        statement = statement.where(Task.completed == completed)
    if priority is not None:
        statement = statement.where(Task.priority == priority.value)
    if category is not None:
        statement = statement.where(Task.category == category.value)
    
    # Order by created_at descending (newest first)
    statement = statement.order_by(Task.created_at.desc())
    
    # Get total count before pagination
    count_statement = select(Task).where(Task.user_id == user_id)
    if completed is not None:
        count_statement = count_statement.where(Task.completed == completed)
    if priority is not None:
        count_statement = count_statement.where(Task.priority == priority.value)
    if category is not None:
        count_statement = count_statement.where(Task.category == category.value)
    
    total_count = len(session.exec(count_statement).all())
    
    # Apply pagination
    offset = (page - 1) * page_size
    statement = statement.offset(offset).limit(page_size)
    
    tasks = session.exec(statement).all()
    
    return TaskListResponse(
        tasks=[TaskResponse.model_validate(task) for task in tasks],
        total_count=total_count,
        page=page,
        page_size=page_size,
    )


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: str,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    """
    Get a specific task by ID for the authenticated user.
    """
    statement = select(Task).where(Task.id == task_id, Task.user_id == user_id)
    task = session.exec(statement).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    
    return task


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: str,
    task_data: TaskUpdate,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    """
    Update an existing task.
    """
    statement = select(Task).where(Task.id == task_id, Task.user_id == user_id)
    task = session.exec(statement).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    
    # Update fields if provided
    update_data = task_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if field == "priority" and value is not None:
            setattr(task, field, value.value)
        elif field == "category" and value is not None:
            setattr(task, field, value.value)
        else:
            setattr(task, field, value)
    
    task.updated_at = datetime.utcnow()
    
    session.add(task)
    session.commit()
    session.refresh(task)
    
    return task


@router.delete("/{task_id}", response_model=MessageResponse)
def delete_task(
    task_id: str,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    """
    Delete a task.
    """
    statement = select(Task).where(Task.id == task_id, Task.user_id == user_id)
    task = session.exec(statement).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    
    session.delete(task)
    session.commit()
    
    return MessageResponse(
        message="Task deleted successfully",
        success=True,
    )


@router.delete("", response_model=MessageResponse)
def delete_all_tasks(
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    """
    Delete all tasks for the authenticated user.
    """
    statement = select(Task).where(Task.user_id == user_id)
    tasks = session.exec(statement).all()
    
    for task in tasks:
        session.delete(task)
    
    session.commit()
    
    return MessageResponse(
        message="All tasks deleted successfully",
        success=True,
    )


@router.patch("/{task_id}/toggle", response_model=TaskResponse)
def toggle_task_completion(
    task_id: str,
    session: Session = Depends(get_session),
    user_id: str = Depends(get_current_user_id),
):
    """
    Toggle the completion status of a task.
    """
    statement = select(Task).where(Task.id == task_id, Task.user_id == user_id)
    task = session.exec(statement).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    
    task.completed = not task.completed
    task.updated_at = datetime.utcnow()
    
    session.add(task)
    session.commit()
    session.refresh(task)
    
    return task

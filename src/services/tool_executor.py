"""
Tool executor for OpenAI function calling in the Todo AI Chatbot.
This module executes task operations directly via service layer functions.
"""
from sqlmodel import Session
from typing import Dict, Any, Optional
from datetime import datetime
import uuid
from fastapi import HTTPException

from src.database.database import get_session
from src.services.task_service import (
    create_task as service_create_task,
    get_task_by_id as service_get_task_by_id,
    update_task as service_update_task,
    delete_task as service_delete_task,
    toggle_task_completion as service_toggle_task,
)
from src.models.task import Task, TaskBase
from src.models.user import User


def get_user_by_id(session: Session, user_id: str) -> Optional[User]:
    """Get user by ID."""
    from sqlmodel import select
    # Ensure user_id is string for SQLite compatibility
    user_id = str(user_id)
    statement = select(User).where(User.id == user_id)
    return session.exec(statement).first()


def find_task_by_title(session: Session, title: str, user_id: str) -> Optional[Task]:
    """Find a task by title for a specific user."""
    from sqlmodel import select
    # Ensure user_id is string for SQLite compatibility
    user_id = str(user_id)
    statement = select(Task).where(
        Task.user_id == user_id,
        Task.title.ilike(f"%{title}%")  # Case-insensitive partial match
    )
    return session.exec(statement).first()


def execute_tool(function_name: str, function_args: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """
    Execute a tool based on function name.
    
    Args:
        function_name: Name of the function to execute
        function_args: Arguments for the function
        user_id: ID of the authenticated user

    Returns:
        Result of the tool execution
    """
    try:
        with next(get_session()) as session:
            if function_name == "create_task":
                return _execute_create_task(session, function_args, user_id)
            elif function_name == "delete_task":
                return _execute_delete_task(session, function_args, user_id)
            elif function_name == "delete_all_tasks":
                return _execute_delete_all_tasks(session, function_args, user_id)
            elif function_name == "update_task":
                return _execute_update_task(session, function_args, user_id)
            elif function_name == "complete_task":
                return _execute_complete_task(session, function_args, user_id)
            elif function_name == "complete_all_tasks":
                return _execute_complete_all_tasks(session, function_args, user_id)
            elif function_name == "list_tasks":
                return _execute_list_tasks(session, user_id)
            else:
                return {
                    "success": False,
                    "error": f"Unknown function: {function_name}"
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def _execute_create_task(session: Session, args: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Execute create_task tool."""
    # Convert user_id to string to fix SQLite UUID binding issue
    user_id = str(user_id)

    title = args.get("title")
    if not title:
        return {"success": False, "error": "Title is required"}

    # Validate title length
    if len(title.strip()) < 2:
        return {"success": False, "error": "Title must be at least 2 characters"}
    if len(title) > 50:
        return {"success": False, "error": "Title must be at most 50 characters"}

    # Verify user exists
    user = get_user_by_id(session, user_id)
    if not user:
        return {"success": False, "error": "User not found"}

    # Create task data - add user_id to args for TaskBase validation
    args['user_id'] = user_id
    
    # Create task data
    task_data = TaskBase(
        title=title.strip(),
        description=args.get("description", ""),
        completed=args.get("completed", False),
        user_id=user_id,
        priority=args.get("priority", "medium"),
        category=args.get("category", "other")
    )

    try:
        task = service_create_task(session, task_data, user_id)
        return {
            "success": True,
            "task_id": str(task.id),
            "title": task.title,
            "message": f"Task '{task.title}' created successfully"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def _execute_delete_task(session: Session, args: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Execute delete_task tool - can use title or task_id."""
    # Convert user_id to string to fix SQLite UUID binding issue
    user_id = str(user_id)

    task_id = args.get("task_id")
    title = args.get("title")

    # If task_id not provided, try to find by title
    if not task_id and title:
        task = find_task_by_title(session, title, user_id)
        if task:
            task_id = str(task.id)
        else:
            return {"success": False, "error": f"No task found with title: {title}"}

    if not task_id:
        return {"success": False, "error": "Either task_id or title is required"}

    try:
        result = service_delete_task(session, task_id, user_id)
        if result:
            return {
                "success": True,
                "task_id": task_id,
                "message": f"Task deleted successfully"
            }
        else:
            return {"success": False, "error": "Failed to delete task"}
    except HTTPException as e:
        return {"success": False, "error": e.detail}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _execute_delete_all_tasks(session: Session, args: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Execute delete_all_tasks tool - deletes all tasks for the user."""
    from sqlmodel import select
    
    # Convert user_id to string to fix SQLite UUID binding issue
    user_id = str(user_id)
    
    try:
        # Fetch all tasks for the user
        statement = select(Task).where(Task.user_id == user_id)
        tasks = session.exec(statement).all()
        
        if not tasks:
            return {
                "success": True,
                "deleted_count": 0,
                "message": "No tasks to delete"
            }
        
        # Delete all tasks
        deleted_count = 0
        for task in tasks:
            session.delete(task)
            deleted_count += 1
        
        # Commit all deletions at once
        session.commit()
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"{deleted_count} task{'s' if deleted_count > 1 else ''} deleted successfully"
        }
    except HTTPException as e:
        return {"success": False, "error": e.detail}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _execute_update_task(session: Session, args: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Execute update_task tool - can use title or task_id."""
    # Convert user_id to string to fix SQLite UUID binding issue
    user_id = str(user_id)
    
    task_id = args.get("task_id")
    title = args.get("title")  # This could be the title to find the task
    new_title = args.get("new_title")

    # Strip whitespace from title for better matching
    if title:
        title = title.strip()
    if new_title:
        new_title = new_title.strip()

    # If task_id not provided, try to find by title
    if not task_id and title:
        task = find_task_by_title(session, title, user_id)
        if task:
            task_id = str(task.id)
        else:
            return {"success": False, "error": f"No task found with title: {title}"}

    if not task_id:
        return {"success": False, "error": "Either task_id or title is required"}

    # Get current task
    task = service_get_task_by_id(session, task_id, user_id)
    if not task:
        return {"success": False, "error": "Task not found"}

    # Prepare update data
    update_data = {
        "title": new_title if new_title else task.title,
        "description": args.get("description", task.description),
        "completed": args.get("completed", task.completed),
        "user_id": user_id,  # Include user_id to fix validation error
        "priority": args.get("priority", task.priority) if hasattr(task, 'priority') else "medium",
        "category": args.get("category", task.category) if hasattr(task, 'category') else "other"
    }

    try:
        task_data = TaskBase(**update_data)
        updated_task = service_update_task(session, task_id, task_data, user_id)
        return {
            "success": True,
            "task_id": str(updated_task.id),
            "title": updated_task.title,
            "message": f"Task '{updated_task.title}' updated successfully"
        }
    except HTTPException as e:
        return {"success": False, "error": e.detail}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _execute_complete_task(session: Session, args: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Execute complete_task tool - can use title or task_id."""
    # Convert user_id to string to fix SQLite UUID binding issue
    user_id = str(user_id)

    task_id = args.get("task_id")
    title = args.get("title")

    # If task_id not provided, try to find by title
    if not task_id and title:
        task = find_task_by_title(session, title, user_id)
        if task:
            task_id = str(task.id)
        else:
            return {"success": False, "error": f"No task found with title: {title}"}

    if not task_id:
        return {"success": False, "error": "Either task_id or title is required"}

    try:
        completed_task = service_toggle_task(session, task_id, user_id)
        return {
            "success": True,
            "task_id": task_id,
            "title": completed_task.title,
            "completed": completed_task.completed,
            "message": f"Task '{completed_task.title}' marked as {'completed' if completed_task.completed else 'pending'}"
        }
    except HTTPException as e:
        return {"success": False, "error": e.detail}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _execute_complete_all_tasks(session: Session, args: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Execute complete_all_tasks tool - marks all pending tasks as completed."""
    from sqlmodel import select
    
    # Convert user_id to string to fix SQLite UUID binding issue
    user_id = str(user_id)
    
    try:
        # Fetch all pending tasks for the user
        statement = select(Task).where(Task.user_id == user_id, Task.completed == False)
        pending_tasks = session.exec(statement).all()
        
        if not pending_tasks:
            return {
                "success": True,
                "completed_count": 0,
                "message": "No pending tasks to mark as complete"
            }
        
        # Mark all pending tasks as completed
        completed_count = 0
        for task in pending_tasks:
            task.completed = True
            session.add(task)
            completed_count += 1
        
        # Commit all changes at once
        session.commit()
        
        return {
            "success": True,
            "completed_count": completed_count,
            "message": f"{completed_count} task{'s' if completed_count > 1 else ''} marked as completed"
        }
    except HTTPException as e:
        return {"success": False, "error": e.detail}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _execute_list_tasks(session: Session, user_id: str) -> Dict[str, Any]:
    """Execute list_tasks tool."""
    from sqlmodel import select

    # Ensure user_id is string for SQLite compatibility
    user_id = str(user_id)
    
    try:
        statement = select(Task).where(Task.user_id == user_id)
        tasks = session.exec(statement).all()

        task_list = []
        for task in tasks:
            task_list.append({
                "id": str(task.id),
                "title": task.title,
                "description": task.description,
                "completed": task.completed,
                "created_at": task.created_at.isoformat() if task.created_at else None
            })

        return {
            "success": True,
            "total_count": len(task_list),
            "tasks": task_list
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

"""
Tool executor for the Todo AI Chatbot application.
Handles execution of task management tools without requiring the MCP server.
"""
import json
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from sqlmodel import Session
from uuid import UUID
from backend.src.database.database import get_session
from backend.src.models.task import Task, TaskBase
from backend.src.services.task_service import (
    get_user_tasks, get_task_by_id, create_task,
    update_task, delete_task, toggle_task_completion
)
import datetime


class AddTaskParams(BaseModel):
    title: str = Field(description="The title/description of the task")
    description: Optional[str] = Field(default=None, description="Detailed description of the task")
    due_date: Optional[str] = Field(default=None, description="Due date in ISO 8601 format (YYYY-MM-DDTHH:mm:ss.sssZ)")
    priority: Optional[str] = Field(default="medium", description="Priority level ('low', 'medium', 'high')")
    category: Optional[str] = Field(default=None, description="Category for organizing tasks")


class ListTasksParams(BaseModel):
    status: Optional[str] = Field(default="all", description="Filter by completion status ('all', 'pending', 'completed')")
    priority: Optional[str] = Field(default=None, description="Filter by priority ('low', 'medium', 'high')")
    category: Optional[str] = Field(default=None, description="Filter by category")
    limit: Optional[int] = Field(default=50, description="Maximum number of tasks to return (max: 100)")
    offset: Optional[int] = Field(default=0, description="Number of tasks to skip for pagination")


class CompleteTaskParams(BaseModel):
    task_id: str = Field(description="The unique identifier of the task to complete")
    completion_notes: Optional[str] = Field(default=None, description="Additional notes about task completion")


class DeleteTaskParams(BaseModel):
    task_id: str = Field(description="The unique identifier of the task to delete")


class UpdateTaskParams(BaseModel):
    task_id: str = Field(description="The unique identifier of the task to update")
    title: Optional[str] = Field(default=None, description="New title for the task")
    description: Optional[str] = Field(default=None, description="New description for the task")
    due_date: Optional[str] = Field(default=None, description="New due date in ISO 8601 format")
    priority: Optional[str] = Field(default=None, description="New priority level ('low', 'medium', 'high')")
    category: Optional[str] = Field(default=None, description="New category for the task")
    completed: Optional[bool] = Field(default=None, description="New completion status")


def execute_add_task(params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """
    Execute the add_task tool.

    Args:
        params: Parameters for the tool
        user_id: ID of the authenticated user

    Returns:
        Result of the tool execution
    """
    try:
        # Validate priority
        priority = params.get('priority', 'medium')
        if priority not in ["low", "medium", "high"]:
            return {
                "success": False,
                "error": "Invalid priority value. Use 'low', 'medium', or 'high'."
            }

        # Parse due date if provided
        due_date_str = params.get('due_date')
        due_date = None
        if due_date_str:
            try:
                from datetime import datetime
                due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
            except ValueError:
                return {
                    "success": False,
                    "error": "Invalid due date format. Use ISO 8601 format (YYYY-MM-DDTHH:mm:ss.sssZ)"
                }

        # Create task data
        task_title = params.get('title', 'Untitled Task')
        task_description = params.get('description')
        task_category = params.get('category')

        # Create a TaskBase object with the provided parameters
        task_to_create = TaskBase(
            title=task_title,
            description=task_description,
            completed=False
        )

        # Get a database session and create the task
        session_gen = get_session()
        session = next(session_gen)
        try:
            db_task = create_task(session, task_to_create, user_id)
            
            result = {
                "success": True,
                "task_id": str(db_task.id),
                "message": f"Task '{db_task.title}' added successfully",
                "task": {
                    "id": str(db_task.id),
                    "title": db_task.title,
                    "description": db_task.description,
                    "completed": db_task.completed,
                    "created_at": db_task.created_at.isoformat(),
                    "updated_at": db_task.updated_at.isoformat()
                    # Note: The current task model doesn't have due_date, priority, or category fields
                }
            }
            return result
        finally:
            session.close()
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to create task: {str(e)}"
        }


def execute_list_tasks(params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """
    Execute the list_tasks tool.

    Args:
        params: Parameters for the tool
        user_id: ID of the authenticated user

    Returns:
        Result of the tool execution
    """
    try:
        # Get a database session and retrieve tasks
        session_gen = get_session()
        session = next(session_gen)
        try:
            # Get all tasks for the user
            tasks = get_user_tasks(session, user_id)
            
            # Apply filters
            status = params.get('status', 'all')
            # Note: The current task model doesn't have priority, so we skip priority filtering
            category = params.get('category')
            limit = min(params.get('limit', 50), 100)  # Max limit of 100
            offset = params.get('offset', 0)
            
            # Filter tasks based on criteria
            filtered_tasks = []
            for task in tasks:
                # Status filter
                if status != 'all':
                    if status == 'completed' and not task.completed:
                        continue
                    elif status == 'pending' and task.completed:
                        continue
                
                # Category filter (skip if task doesn't have category attribute)
                if category and hasattr(task, 'category') and task.category != category:
                    continue
                
                filtered_tasks.append(task)
            
            # Apply pagination
            paginated_tasks = filtered_tasks[offset:offset + limit]
            
            # Convert tasks to dictionary format
            task_list = []
            for task in paginated_tasks:
                task_dict = {
                    "id": str(task.id),
                    "title": task.title,
                    "description": task.description,
                    "completed": task.completed,
                    "created_at": task.created_at.isoformat(),
                    "updated_at": task.updated_at.isoformat()
                    # Note: The current task model doesn't have due_date, priority, or category fields
                }
                task_list.append(task_dict)

            result = {
                "success": True,
                "total_count": len(filtered_tasks),
                "returned_count": len(task_list),
                "tasks": task_list
            }
            return result
        finally:
            session.close()
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to retrieve tasks: {str(e)}"
        }


def execute_complete_task(params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """
    Execute the complete_task tool.

    Args:
        params: Parameters for the tool
        user_id: ID of the authenticated user

    Returns:
        Result of the tool execution
    """
    try:
        task_id = params.get('task_id')
        if not task_id:
            return {
                "success": False,
                "error": "task_id is required"
            }

        # Get a database session and toggle task completion
        session_gen = get_session()
        session = next(session_gen)
        try:
            db_task = toggle_task_completion(session, task_id, user_id)
            
            result = {
                "success": True,
                "task_id": str(db_task.id),
                "message": f"Task '{db_task.title}' marked as {'completed' if db_task.completed else 'pending'}",
                "task": {
                    "id": str(db_task.id),
                    "title": db_task.title,
                    "description": db_task.description,
                    "completed": db_task.completed,
                    "created_at": db_task.created_at.isoformat(),
                    "updated_at": db_task.updated_at.isoformat()
                    # Note: The current task model doesn't have due_date, priority, or category fields
                }
            }
            return result
        finally:
            session.close()
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to complete task: {str(e)}"
        }


def execute_delete_task(params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """
    Execute the delete_task tool.

    Args:
        params: Parameters for the tool
        user_id: ID of the authenticated user

    Returns:
        Result of the tool execution
    """
    try:
        task_id = params.get('task_id')
        if not task_id:
            return {
                "success": False,
                "error": "task_id is required"
            }

        # Get a database session and delete the task
        session_gen = get_session()
        session = next(session_gen)
        try:
            success = delete_task(session, task_id, user_id)
            
            if success:
                result = {
                    "success": True,
                    "task_id": task_id,
                    "message": f"Task {task_id} deleted successfully"
                }
            else:
                result = {
                    "success": False,
                    "error": "Task not found or does not belong to user"
                }
                
            return result
        finally:
            session.close()
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to delete task: {str(e)}"
        }


def execute_update_task(params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """
    Execute the update_task tool.

    Args:
        params: Parameters for the tool
        user_id: ID of the authenticated user

    Returns:
        Result of the tool execution
    """
    try:
        task_id = params.get('task_id')
        if not task_id:
            return {
                "success": False,
                "error": "task_id is required"
            }

        # Get a database session and update the task
        session_gen = get_session()
        session = next(session_gen)
        try:
            # Get the existing task to update
            existing_task = get_task_by_id(session, task_id, user_id)
            if not existing_task:
                return {
                    "success": False,
                    "error": "Task not found or does not belong to user"
                }

            # Prepare update data
            update_data = {}
            if 'title' in params and params['title'] is not None:
                update_data['title'] = params['title']
            if 'description' in params and params['description'] is not None:
                update_data['description'] = params['description']
            if 'due_date' in params and params['due_date'] is not None:
                due_date_str = params['due_date']
                try:
                    from datetime import datetime
                    due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                    update_data['due_date'] = due_date
                except ValueError:
                    return {
                        "success": False,
                        "error": "Invalid due date format. Use ISO 8601 format (YYYY-MM-DDTHH:mm:ss.sssZ)"
                    }
            # Skip priority update since the current task model doesn't have priority
            if 'category' in params and params['category'] is not None:
                update_data['category'] = params['category']
            if 'completed' in params and params['completed'] is not None:
                update_data['completed'] = params['completed']

            # Create a TaskBase object with the update data
            # Note: The current task model doesn't have priority or due_date fields
            task_to_update = TaskBase(
                title=update_data.get('title', existing_task.title),
                description=update_data.get('description', existing_task.description or None),
                completed=update_data.get('completed', existing_task.completed),
                user_id=existing_task.user_id  # Preserve the user_id
            )

            # Perform the update
            updated_task = update_task(session, task_id, task_to_update, user_id)
            
            result = {
                "success": True,
                "task_id": str(updated_task.id),
                "message": f"Task '{updated_task.title}' updated successfully",
                "task": {
                    "id": str(updated_task.id),
                    "title": updated_task.title,
                    "description": updated_task.description,
                    "completed": updated_task.completed,
                    "created_at": updated_task.created_at.isoformat(),
                    "updated_at": updated_task.updated_at.isoformat()
                    # Note: The current task model doesn't have due_date, priority, or category fields
                }
            }
            return result
        finally:
            session.close()
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to update task: {str(e)}"
        }


def execute_tool(tool_name: str, params: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """
    Execute a tool by name.

    Args:
        tool_name: Name of the tool to execute
        params: Parameters for the tool
        user_id: ID of the authenticated user

    Returns:
        Result of the tool execution
    """
    if tool_name == "add_task":
        return execute_add_task(params, user_id)
    elif tool_name == "list_tasks":
        return execute_list_tasks(params, user_id)
    elif tool_name == "complete_task":
        return execute_complete_task(params, user_id)
    elif tool_name == "delete_task":
        return execute_delete_task(params, user_id)
    elif tool_name == "update_task":
        return execute_update_task(params, user_id)
    else:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}"
        }
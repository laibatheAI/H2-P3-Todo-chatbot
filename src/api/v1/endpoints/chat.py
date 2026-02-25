"""
Chat API endpoint for the Todo AI Chatbot application.
This endpoint handles authenticated chat requests and integrates with the AI agent.
"""
from fastapi import APIRouter, Path, HTTPException, status, Body, Request, Depends
from typing import Dict, Any, List, Optional
import time
import uuid
import json
from datetime import datetime
from openai import OpenAI
from openai import APIError, RateLimitError, AuthenticationError, PermissionDeniedError, NotFoundError, APIConnectionError, APITimeoutError
import os

# Import OpenRouter fallback client
from src.services.openrouter_client import (
    call_openrouter_chat,
    is_openrouter_configured,
    get_openrouter_model_name
)

# Import models with error handling
try:
    from src.schemas.chat import ChatRequest, ChatResponse, AssistantMessage, ResponseMetadata
except ImportError:
    # Define fallback models if schema doesn't exist
    from pydantic import BaseModel

    class Message(BaseModel):
        content: str
        role: str = "user"

    class ChatRequest(BaseModel):
        message: Message

    class AssistantMessage(BaseModel):
        role: str
        content: str
        tool_calls: list = []
        tool_results: list = []

    class ResponseMetadata(BaseModel):
        processing_time_ms: int

    class ChatResponse(BaseModel):
        conversation_id: str
        response: AssistantMessage
        timestamp: datetime
        metadata: ResponseMetadata

# Import JWT service for token verification
from src.services.jwt_service import verify_token, get_user_id_from_token

# Import tool executor
from src.services.tool_executor import execute_tool

router = APIRouter()


def should_use_fallback(error: Exception) -> bool:
    """
    Check if the error should trigger OpenRouter fallback.
    
    Returns True only for:
    - insufficient_quota (429)
    - model_not_found (404)
    - permission_denied for model access (403)
    """
    if isinstance(error, RateLimitError):
        error_detail = str(error).lower()
        if "insufficient_quota" in error_detail:
            return True
    
    if isinstance(error, NotFoundError):
        error_detail = str(error).lower()
        if "model" in error_detail:
            return True
    
    if isinstance(error, PermissionDeniedError):
        error_detail = str(error).lower()
        if "model" in error_detail or "access" in error_detail:
            return True
    
    return False


def handle_openai_error(error: Exception) -> tuple[str, int]:
    """
    Handle OpenAI API errors and return appropriate user-friendly messages.

    Args:
        error: The OpenAI exception that was raised

    Returns:
        Tuple of (user_message, status_code)
    """
    # Rate limit / quota exceeded errors
    if isinstance(error, RateLimitError):
        error_detail = str(error)
        if "insufficient_quota" in error_detail.lower():
            print("❌ OpenAI Error: Insufficient quota (429)")
            print(f"   Full error: {error_detail}")
            return (
                "Sorry! OpenAI usage limit reached. Please wait a few minutes or contact the administrator to check billing/usage. "
                "For more info: https://platform.openai.com/account/usage",
                status.HTTP_503_SERVICE_UNAVAILABLE
            )
        else:
            print("❌ OpenAI Error: Rate limit exceeded (429)")
            print(f"   Full error: {error_detail}")
            return (
                "Too many requests. Please wait a moment and try again.",
                status.HTTP_429_TOO_MANY_REQUESTS
            )

    # Authentication errors (invalid API key)
    elif isinstance(error, AuthenticationError):
        print("❌ OpenAI Error: Authentication failed (401)")
        print(f"   Full error: {str(error)}")
        return (
            "OpenAI authentication failed. Please contact the administrator to verify the API key configuration.",
            status.HTTP_503_SERVICE_UNAVAILABLE
        )

    # Permission errors (API key doesn't have access to model)
    elif isinstance(error, PermissionDeniedError):
        print("❌ OpenAI Error: Permission denied (403)")
        print(f"   Full error: {str(error)}")
        return (
            "OpenAI API key doesn't have access to this model. Please contact the administrator.",
            status.HTTP_503_SERVICE_UNAVAILABLE
        )

    # Model not found errors
    elif isinstance(error, NotFoundError):
        print("❌ OpenAI Error: Model not found (404)")
        print(f"   Full error: {str(error)}")
        return (
            "OpenAI model configuration error. Please contact the administrator.",
            status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    # Connection errors
    elif isinstance(error, APIConnectionError):
        print("❌ OpenAI Error: Connection failed")
        print(f"   Full error: {str(error)}")
        return (
            "Cannot connect to OpenAI service. Please try again in a few moments.",
            status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    # Timeout errors
    elif isinstance(error, APITimeoutError):
        print("❌ OpenAI Error: Request timeout")
        print(f"   Full error: {str(error)}")
        return (
            "OpenAI request timed out. Please try again.",
            status.HTTP_504_GATEWAY_TIMEOUT
        )
    
    # Generic API errors
    elif isinstance(error, APIError):
        print(f"❌ OpenAI Error: API error ({error.status_code or 'unknown'})")
        print(f"   Full error: {str(error)}")
        return (
            f"OpenAI service error. Please try again later. ({error.status_code or 'unknown error'})",
            status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    # Unknown errors
    else:
        print("❌ OpenAI Error: Unexpected error")
        print(f"   Full error: {str(error)}")
        return (
            "An unexpected error occurred while processing your request. Please try again.",
            status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# OpenAI client setup - Read API key from src/.env file
def load_openai_api_key() -> str:
    """
    Load OpenAI API key from src/.env file.
    This ensures the API key is read from the project's .env file
    without requiring manual environment variable configuration.
    """
    import os
    from pathlib import Path
    
    # Get the directory structure:
    # This file is at: project_root/src/api/v1/endpoints/chat.py
    # We want to load from: project_root/src/.env
    
    # Navigate to src/ directory (3 levels up from this file)
    src_dir = Path(__file__).parent.parent.parent  # Goes to: project_root/src/
    src_env_path = src_dir / ".env"
    
    # Strategy 1: Load from src/.env
    if src_env_path.exists():
        from dotenv import dotenv_values
        env_vars = dotenv_values(src_env_path)
        api_key = env_vars.get("OPENAI_API_KEY", "").strip()
        if api_key:
            print(f"[INFO] Loaded OPENAI_API_KEY from src/.env (length: {len(api_key)} chars)")
            return api_key
    
    # Strategy 2: Try loading from project root .env
    project_root = src_dir.parent  # Goes to: project_root/
    root_env_path = project_root / ".env"
    if root_env_path.exists():
        from dotenv import dotenv_values
        env_vars = dotenv_values(root_env_path)
        api_key = env_vars.get("OPENAI_API_KEY", "").strip()
        if api_key:
            print(f"[INFO] Loaded OPENAI_API_KEY from root .env (length: {len(api_key)} chars)")
            return api_key
    
    # Strategy 3: Fallback to environment variable
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if api_key:
        print(f"[INFO] Loaded OPENAI_API_KEY from environment variable")
        return api_key
    
    print("[WARN] OPENAI_API_KEY not found in any location")
    return ""

OPENAI_API_KEY = load_openai_api_key()
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def get_system_prompt() -> str:
    """Return the system prompt for the AI assistant."""
    return """You are a helpful and efficient Todo AI Assistant. Your role is to help users manage their tasks through natural language conversations.

You have access to the following tools:
- create_task: Creates a new task with a title and optional description
- delete_task: Deletes a task by title or task_id
- update_task: Updates a task's properties (title, description, completed status)
- complete_task: Marks a task as completed or pending
- list_tasks: Lists all tasks for the user

When the user wants to:
- Add/create a task → use create_task with the title
- Remove/delete a task → use delete_task with the title
- Mark done/complete a task → use complete_task with the title
- Change/update a task → use update_task
- See/show tasks → use list_tasks

Always confirm what action you're taking. Be concise and helpful."""


def get_available_tools() -> List[Dict[str, Any]]:
    """Return the list of available tools for OpenAI function calling."""
    return [
        {
            "type": "function",
            "function": {
                "name": "create_task",
                "description": "Creates a new task in the user's task list",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "The title of the task (required, 2-50 characters)"
                        },
                        "description": {
                            "type": "string",
                            "description": "Optional description of the task"
                        }
                    },
                    "required": ["title"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "delete_task",
                "description": "Deletes a specific task from the user's task list",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "The title of the task to delete"
                        },
                        "task_id": {
                            "type": "string",
                            "description": "The ID of the task to delete (if known)"
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "delete_all_tasks",
                "description": "Deletes ALL tasks from the user's task list. Use this when user wants to delete all tasks at once.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "update_task",
                "description": "Updates properties of an existing task",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Current title of the task to find it"
                        },
                        "new_title": {
                            "type": "string",
                            "description": "New title for the task"
                        },
                        "description": {
                            "type": "string",
                            "description": "New description for the task"
                        },
                        "completed": {
                            "type": "boolean",
                            "description": "Mark task as completed (true) or pending (false)"
                        }
                    },
                    "required": ["title"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "complete_task",
                "description": "Marks a specific task as completed",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "The title of the task to complete"
                        },
                        "task_id": {
                            "type": "string",
                            "description": "The ID of the task to complete (if known)"
                        }
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "complete_all_tasks",
                "description": "Marks ALL pending tasks as completed. Use this when user wants to complete multiple tasks at once.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "list_tasks",
                "description": "Lists all tasks for the user",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        }
    ]


async def call_ai_with_fallback(
    messages: List[Dict[str, Any]],
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: str = "auto",
    model: str = "gpt-3.5-turbo",
    max_tokens: int = 1000,
    temperature: float = 0.7
):
    """
    Call AI model with automatic fallback to OpenRouter when OpenAI fails.
    
    This function:
    1. Tries OpenAI first
    2. If OpenAI fails due to quota/model issues, falls back to OpenRouter
    3. Returns response in OpenAI-compatible format
    
    Args:
        messages: List of message dictionaries
        tools: Optional list of tool definitions
        tool_choice: Tool choice strategy
        model: Model name for OpenAI
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
    
    Returns:
        Response object with choices[0].message structure
    
    Raises:
        HTTPException: If both providers fail
    """
    # Try OpenAI first
    if openai_client:
        try:
            print(f"📞 Calling OpenAI model: {model}")
            response = openai_client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
                max_tokens=max_tokens,
                temperature=temperature
            )
            print(f"✅ OpenAI response received")
            return response
        except Exception as e:
            # Check if we should use fallback
            if should_use_fallback(e):
                print(f"⚠️  OpenAI failed ({type(e).__name__}), switching to OpenRouter fallback...")
            else:
                # Not a fallback error, re-raise
                raise
    
    # Fallback to OpenRouter
    if is_openrouter_configured():
        try:
            fallback_model = get_openrouter_model_name()
            print(f"📞 Calling OpenRouter fallback model: {fallback_model}")
            
            response = await call_openrouter_chat(
                messages=messages,
                tools=tools,
                tool_choice=tool_choice
            )
            print(f"✅ OpenRouter response received")
            return response
        except Exception as fallback_error:
            print(f"❌ OpenRouter fallback also failed: {fallback_error}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI service temporarily unavailable. Please try again later."
            )
    else:
        # No fallback configured
        print("❌ OpenRouter fallback not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenAI service is currently unavailable. Please try again later."
        )


def get_current_user_from_request(request: Request) -> str:
    """
    Extract and validate the current user ID from the Authorization header.
    
    This is a dependency function that:
    1. Extracts the Bearer token from Authorization header
    2. Validates the JWT token
    3. Returns the user_id from the token payload
    
    Raises:
        HTTPException: 401 if token is missing, invalid, or expired
    """
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing or malformed",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = auth_header[7:]  # Remove "Bearer " prefix
    
    # Verify the token
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user_id from token
    user_id = get_user_id_from_token(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: user_id not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


@router.post("/{user_id}/chat", tags=["chat"])
async def chat_endpoint(
    request: Request,
    user_id: str = Path(..., description="The unique identifier of the authenticated user"),
    chat_request: ChatRequest = Body(...),
    current_user_id: str = Depends(get_current_user_from_request)
) -> ChatResponse:
    """
    Chat endpoint that processes user messages and returns AI-generated responses.
    Uses OpenAI function calling to execute task operations.
    
    Flow:
    1. Validate authentication via JWT token (dependency injection)
    2. Verify URL user_id matches JWT user_id
    3. Call OpenAI with tools
    4. Execute tools directly (no HTTP call)
    5. Database is updated
    6. Confirmation response is returned
    
    Raises:
        HTTPException: 401 if not authenticated, 403 if user_id mismatch
    """
    print("🔥 CHAT ENDPOINT HIT")
    start_time = time.time()

    # CRITICAL: Verify that the URL user_id matches the JWT user_id
    if current_user_id != user_id:
        print(f"❌ User ID mismatch: URL={user_id}, JWT={current_user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: User ID mismatch. URL user_id ({user_id}) does not match authenticated user ({current_user_id})",
        )

    # Convert user_id to string to fix SQLite UUID binding issue
    # This ensures all downstream database queries receive string, not UUID object
    user_id = str(user_id)
    
    print(f"✅ Authenticated user: {current_user_id}")

    try:
        # Build messages for OpenAI
        messages = [
            {"role": "system", "content": get_system_prompt()},
            {"role": "user", "content": chat_request.message.content}
        ]

        # Call AI with fallback to OpenRouter
        response = await call_ai_with_fallback(
            messages=messages,
            tools=get_available_tools(),
            tool_choice="auto",
            model="gpt-3.5-turbo",
            max_tokens=1000,
            temperature=0.7
        )

        assistant_message = response.choices[0].message
        tool_calls = assistant_message.tool_calls
        tool_results = []

        # If OpenAI wants to call a tool, execute it
        if tool_calls:
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                print(f"🔧 Executing tool: {function_name}")
                print(f"   Args: {function_args}")

                # Execute the tool directly (no HTTP call)
                result = execute_tool(function_name, function_args, current_user_id)

                print(f"   Result: {result}")

                tool_results.append({
                    "tool_call_id": tool_call.id,
                    "result": result
                })

            # After executing tools, get final response from OpenAI
            messages.append({
                "role": "assistant",
                "content": assistant_message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in tool_calls
                ]
            })

            # Add tool results to messages
            for tool_result in tool_results:
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_result["tool_call_id"],
                    "content": json.dumps(tool_result["result"])
                })

            # Get final response after tool execution (with fallback)
            final_response = await call_ai_with_fallback(
                messages=messages,
                tools=None,  # No tools needed for final response
                tool_choice="none",
                model="gpt-3.5-turbo",
                max_tokens=500,
                temperature=0.7
            )

            response_content = final_response.choices[0].message.content or ""
        else:
            # No tool calls, just use the direct response
            response_content = assistant_message.content or ""

        # Build the response
        processing_time_ms = int((time.time() - start_time) * 1000)
        conversation_id = str(uuid.uuid4())

        # Format tool calls for response
        formatted_tool_calls = []
        if tool_calls:
            for tc in tool_calls:
                formatted_tool_calls.append({
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                })

        assistant_msg = AssistantMessage(
            role="assistant",
            content=response_content,
            tool_calls=formatted_tool_calls,
            tool_results=tool_results
        )

        return ChatResponse(
            conversation_id=conversation_id,
            response=assistant_msg,
            timestamp=datetime.utcnow(),
            metadata=ResponseMetadata(processing_time_ms=processing_time_ms)
        )

    except HTTPException:
        # Re-raise HTTP exceptions (auth errors, etc.)
        raise
    
    # Handle specific OpenAI API errors with user-friendly messages
    except RateLimitError as e:
        user_msg, status_code = handle_openai_error(e)
        raise HTTPException(status_code=status_code, detail=user_msg)
    
    except AuthenticationError as e:
        user_msg, status_code = handle_openai_error(e)
        raise HTTPException(status_code=status_code, detail=user_msg)
    
    except PermissionDeniedError as e:
        user_msg, status_code = handle_openai_error(e)
        raise HTTPException(status_code=status_code, detail=user_msg)
    
    except NotFoundError as e:
        user_msg, status_code = handle_openai_error(e)
        raise HTTPException(status_code=status_code, detail=user_msg)
    
    except APIConnectionError as e:
        user_msg, status_code = handle_openai_error(e)
        raise HTTPException(status_code=status_code, detail=user_msg)
    
    except APITimeoutError as e:
        user_msg, status_code = handle_openai_error(e)
        raise HTTPException(status_code=status_code, detail=user_msg)
    
    except APIError as e:
        user_msg, status_code = handle_openai_error(e)
        raise HTTPException(status_code=status_code, detail=user_msg)
    
    except Exception as e:
        # Catch-all for unexpected errors
        print(f"❌ Unexpected error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred. Please try again later."
        )


@router.get("/health", tags=["chat"])
async def chat_health_check():
    """Health check endpoint for the chat service."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "service": "todo-chatbot-chat-api"
    }
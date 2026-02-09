"""
Chat API endpoint for the Todo AI Chatbot application.
This endpoint handles authenticated chat requests and integrates with the AI agent.
"""
from fastapi import APIRouter, Path, HTTPException, status, Body, Depends, Request
from typing import Dict, Any
import time
import uuid
from datetime import datetime

from backend.schemas.chat import ChatRequest, ChatResponse, AssistantMessage, ResponseMetadata
from backend.middleware.auth import jwt_auth, get_current_user_id
from backend.middleware.auth_validation import validate_authenticated_request
from backend.core.agents.chat_agent import get_default_agent
from backend.utils.conversation_loader import load_conversation_history, save_message_to_conversation


router = APIRouter()


@router.post("/api/{user_id}/chat", response_model=ChatResponse, tags=["chat"])
async def chat_endpoint(
    request: Request,
    user_id: str = Path(..., description="The unique identifier of the authenticated user"),
    chat_request: ChatRequest = Body(...)
) -> ChatResponse:
    """
    Chat endpoint that processes user messages and returns AI-generated responses.
    Validates authentication and integrates with the AI agent for task management.
    """
    start_time = time.time()

    # Validate authentication
    token_data = validate_authenticated_request(request)
    
    # Verify that the user_id in the path matches the authenticated user
    if token_data.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: User ID mismatch"
        )

    # Load conversation history (in a stateless manner, this would typically come from DB)
    # For now, we'll use an empty history since we're implementing stateless architecture
    conversation_history = []

    # Get the user's message from the request
    user_message = chat_request.message.content

    # Initialize the agent
    agent = get_default_agent()

    # Process the message with the agent
    agent_response = await agent.process_message(
        user_message=user_message,
        conversation_history=conversation_history,
        user_id=user_id
    )

    # Generate a conversation ID for this interaction
    conversation_id = str(uuid.uuid4())

    # Calculate processing time
    processing_time_ms = int((time.time() - start_time) * 1000)

    # Create the assistant message response
    assistant_message = AssistantMessage(
        role=agent_response["role"],
        content=agent_response["content"],
        tool_calls=agent_response.get("tool_calls", []),
        tool_results=agent_response.get("tool_results", [])
    )

    response = ChatResponse(
        conversation_id=conversation_id,
        response=assistant_message,
        timestamp=datetime.utcnow(),
        metadata=ResponseMetadata(processing_time_ms=processing_time_ms)
    )

    return response


@router.get("/api/{user_id}/health", tags=["chat"])
async def chat_health_check(
    request: Request,
    user_id: str = Path(..., description="The unique identifier of the user (for path validation)")
):
    """
    Health check endpoint for the chat service.
    """
    # Even for health check, we might want to validate the user is authenticated
    # But for this endpoint, we'll just validate the token if present
    auth_header = request.headers.get("Authorization")
    auth_status = "no auth required"
    
    if auth_header:
        try:
            token_data = validate_authenticated_request(request)
            auth_status = "authenticated"
        except:
            auth_status = "invalid token"
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "service": "todo-chatbot-chat-api",
        "auth_status": auth_status
    }
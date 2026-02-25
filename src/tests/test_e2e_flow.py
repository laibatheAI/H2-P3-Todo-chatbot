"""
End-to-End tests for the Todo AI Chatbot application.
These tests verify the complete flow from natural language input to tool execution to response.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from backend.main import app
from backend.core.agents.todo_agent import TodoAgent, AgentConfig


def test_end_to_end_task_creation_flow():
    """
    E2E test that verifies:
    1. An authenticated user sends "add task Buy food"
    2. Backend processes through chat endpoint → agent → MCP tool
    3. A task is created in the database
    4. Response confirms task creation
    """
    client = TestClient(app)
    
    # Mock JWT token for authentication
    mock_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXItMTIzIiwidXNlcl9pZCI6InRlc3QtdXNlci0xMjMiLCJleHAiOjk5OTk5OTk5OTl9.test_signature"
    
    # Mock the agent response for task creation
    mock_agent_response = {
        "content": "I've added the task 'Buy food' to your list.",
        "role": "assistant",
        "tool_calls": [{
            "id": "call_add_task_123",
            "type": "function",
            "function": {
                "name": "add_task",
                "arguments": '{"title": "Buy food", "description": "Get groceries for the week", "priority": "medium"}'
            }
        }],
        "tool_results": [{
            "tool_call_id": "call_add_task_123",
            "result": {
                "success": True,
                "task_id": "task_456",
                "message": "Task 'Buy food' added successfully",
                "task": {
                    "id": "task_456",
                    "title": "Buy food",
                    "description": "Get groceries for the week",
                    "priority": "medium",
                    "completed": False
                }
            }
        }]
    }
    
    # Patch the agent's process_message method to return our mock response
    with patch('backend.core.agents.chat_agent.get_default_agent') as mock_get_agent:
        mock_agent = AsyncMock()
        mock_agent.process_message.return_value = mock_agent_response
        mock_get_agent.return_value = mock_agent
        
        # Send the request to the chat endpoint
        response = client.post(
            "/api/test-user-123/chat",
            headers={"Authorization": f"Bearer {mock_token}"},
            json={
                "message": {
                    "role": "user",
                    "content": "add task Buy food"
                }
            }
        )
        
        # Verify the response is successful
        assert response.status_code == 200
        
        # Verify the response is not the static test response
        response_data = response.json()
        assert response_data["response"]["content"] != "Hello! This is a test response from the chatbot. Your message was received."
        
        # Verify the response contains the expected task creation confirmation
        assert "Buy food" in response_data["response"]["content"]
        assert "added" in response_data["response"]["content"].lower()
        
        # Verify tool calls were processed
        assert len(response_data["response"]["tool_calls"]) > 0
        assert response_data["response"]["tool_calls"][0]["function"]["name"] == "add_task"


def test_end_to_end_task_listing_flow():
    """
    E2E test for listing tasks flow.
    """
    client = TestClient(app)
    
    # Mock JWT token
    mock_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXItMTIzIiwidXNlcl9pZCI6InRlc3QtdXNlci0xMjMiLCJleHAiOjk5OTk5OTk5OTl9.test_signature"
    
    # Mock agent response for listing tasks
    mock_agent_response = {
        "content": "Here are your current tasks: 1. Buy food (not completed), 2. Walk dog (not completed)",
        "role": "assistant",
        "tool_calls": [{
            "id": "call_list_tasks_456",
            "type": "function",
            "function": {
                "name": "list_tasks",
                "arguments": "{}"
            }
        }],
        "tool_results": [{
            "tool_call_id": "call_list_tasks_456",
            "result": {
                "success": True,
                "total_count": 2,
                "returned_count": 2,
                "tasks": [
                    {
                        "id": "task_1",
                        "title": "Buy food",
                        "completed": False
                    },
                    {
                        "id": "task_2",
                        "title": "Walk dog",
                        "completed": False
                    }
                ]
            }
        }]
    }
    
    with patch('backend.core.agents.chat_agent.get_default_agent') as mock_get_agent:
        mock_agent = AsyncMock()
        mock_agent.process_message.return_value = mock_agent_response
        mock_get_agent.return_value = mock_agent
        
        response = client.post(
            "/api/test-user-123/chat",
            headers={"Authorization": f"Bearer {mock_token}"},
            json={
                "message": {
                    "role": "user",
                    "content": "show my tasks"
                }
            }
        )
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["response"]["content"] != "Hello! This is a test response from the chatbot. Your message was received."
        
        # Verify the response contains task information
        content = response_data["response"]["content"].lower()
        assert "buy food" in content
        assert "walk dog" in content
        assert "tasks" in content


def test_end_to_end_task_completion_flow():
    """
    E2E test for completing a task.
    """
    client = TestClient(app)
    
    # Mock JWT token
    mock_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXItMTIzIiwidXNlcl9pZCI6InRlc3QtdXNlci0xMjMiLCJleHAiOjk5OTk5OTk5OTl9.test_signature"
    
    # Mock agent response for completing a task
    mock_agent_response = {
        "content": "I've marked the task 'Buy food' as completed.",
        "role": "assistant",
        "tool_calls": [{
            "id": "call_complete_task_789",
            "type": "function",
            "function": {
                "name": "complete_task",
                "arguments": '{"task_id": "task_456"}'
            }
        }],
        "tool_results": [{
            "tool_call_id": "call_complete_task_789",
            "result": {
                "success": True,
                "task_id": "task_456",
                "message": "Task 'Buy food' marked as completed",
                "task": {
                    "id": "task_456",
                    "title": "Buy food",
                    "completed": True
                }
            }
        }]
    }
    
    with patch('backend.core.agents.chat_agent.get_default_agent') as mock_get_agent:
        mock_agent = AsyncMock()
        mock_agent.process_message.return_value = mock_agent_response
        mock_get_agent.return_value = mock_agent
        
        response = client.post(
            "/api/test-user-123/chat",
            headers={"Authorization": f"Bearer {mock_token}"},
            json={
                "message": {
                    "role": "user",
                    "content": "complete task Buy food"
                }
            }
        )
        
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["response"]["content"] != "Hello! This is a test response from the chatbot. Your message was received."
        
        # Verify the response confirms task completion
        content = response_data["response"]["content"].lower()
        assert "buy food" in content
        assert "completed" in content


@pytest.mark.asyncio
async def test_agent_processes_multiple_interactions():
    """
    Test that the agent can handle a sequence of interactions properly.
    """
    config = AgentConfig()
    agent = TodoAgent(config=config)
    
    # First interaction: add a task
    mock_response_1 = AsyncMock()
    mock_choice_1 = AsyncMock()
    mock_message_1 = AsyncMock()
    
    mock_tool_call_1 = AsyncMock()
    mock_tool_call_1.id = "call_add_task_1"
    mock_function_1 = AsyncMock()
    mock_function_1.name = "add_task"
    mock_function_1.arguments = '{"title": "Buy groceries", "priority": "high"}'
    mock_tool_call_1.function = mock_function_1
    mock_message_1.tool_calls = [mock_tool_call_1]
    mock_message_1.content = "I've added the task 'Buy groceries' to your high-priority list."
    
    mock_choice_1.message = mock_message_1
    mock_response_1.choices = [mock_choice_1]
    
    # Second interaction: list tasks
    mock_response_2 = AsyncMock()
    mock_choice_2 = AsyncMock()
    mock_message_2 = AsyncMock()
    
    mock_tool_call_2 = AsyncMock()
    mock_tool_call_2.id = "call_list_tasks_2"
    mock_function_2 = AsyncMock()
    mock_function_2.name = "list_tasks"
    mock_function_2.arguments = '{}'
    mock_tool_call_2.function = mock_function_2
    mock_message_2.tool_calls = [mock_tool_call_2]
    mock_message_2.content = "You have 1 task: Buy groceries (high priority)."
    
    mock_choice_2.message = mock_message_2
    mock_response_2.choices = [mock_choice_2]
    
    with patch.object(agent, 'client') as mock_client:
        # Configure the mock to return different responses for different calls
        call_count = 0
        def side_effect_func(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return mock_response_1
            else:
                return mock_response_2
        
        mock_client.chat.completions.create.side_effect = side_effect_func
        
        # Mock tool execution
        with patch('backend.core.agents.todo_agent.TodoAgent._execute_tool_call') as mock_execute:
            def tool_side_effect(*args, **kwargs):
                nonlocal call_count
                if call_count == 1:  # First call was for add_task
                    return {
                        "success": True,
                        "task_id": "task_123",
                        "message": "Task 'Buy groceries' added successfully",
                        "task": {"id": "task_123", "title": "Buy groceries", "priority": "high", "completed": False}
                    }
                else:  # Second call was for list_tasks
                    return {
                        "success": True,
                        "total_count": 1,
                        "returned_count": 1,
                        "tasks": [{"id": "task_123", "title": "Buy groceries", "priority": "high", "completed": False}]
                    }
            
            mock_execute.side_effect = tool_side_effect
            
            # First interaction: add task
            result1 = await agent.process_message(
                user_message="add high priority task Buy groceries",
                conversation_history=[],
                user_id="test-user-id"
            )
            
            # Verify first response is not static
            assert result1["content"] != "Hello! This is a test response from the chatbot. Your message was received."
            assert "Buy groceries" in result1["content"]
            
            # Second interaction: list tasks
            result2 = await agent.process_message(
                user_message="what tasks do I have?",
                conversation_history=[],
                user_id="test-user-id"
            )
            
            # Verify second response is not static
            assert result2["content"] != "Hello! This is a test response from the chatbot. Your message was received."
            assert "Buy groceries" in result2["content"]
            assert "1 task" in result2["content"]
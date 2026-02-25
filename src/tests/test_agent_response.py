"""
Unit tests for verifying the AI agent response in the Todo AI Chatbot application.
These tests ensure that the agent is returning dynamic responses from the AI model
rather than static/fallback responses.
"""
import pytest
from unittest.mock import AsyncMock, patch
from backend.core.agents.todo_agent import TodoAgent, AgentConfig


@pytest.mark.asyncio
async def test_agent_returns_dynamic_response_instead_of_static():
    """
    Test that the agent returns a dynamic AI-generated response
    and NOT the static test response.
    """
    # Create agent with mocked OpenAI client to simulate API response
    config = AgentConfig()
    agent = TodoAgent(config=config)
    
    # Mock the OpenAI client response
    mock_response = AsyncMock()
    mock_choice = AsyncMock()
    mock_message = AsyncMock()
    
    # Set up a realistic AI-generated response (not the static test response)
    mock_message.content = "Sure, I can help you with that. What would you like to do?"
    mock_message.tool_calls = None
    
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    
    # Patch the OpenAI client to return our mock response
    with patch.object(agent, 'client') as mock_client:
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test the agent with a simple input
        result = await agent.process_message(
            user_message="hello",
            conversation_history=[],
            user_id="test-user-id"
        )
        
        # Verify that the response is NOT the static test response
        assert result["content"] != "Hello! This is a test response from the chatbot. Your message was received."
        
        # Verify that the response contains dynamic content
        assert "help" in result["content"].lower() or "hello" in result["content"].lower()
        assert result["role"] == "assistant"


@pytest.mark.asyncio
async def test_agent_handles_different_inputs():
    """
    Test that the agent returns different responses for different inputs
    (indicating it's actually processing the input, not returning static text).
    """
    config = AgentConfig()
    agent = TodoAgent(config=config)
    
    # Create mock response objects
    def create_mock_response(content):
        mock_response = AsyncMock()
        mock_choice = AsyncMock()
        mock_message = AsyncMock()
        mock_message.content = content
        mock_message.tool_calls = None
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        return mock_response
    
    with patch.object(agent, 'client') as mock_client:
        # Configure the mock to return different responses based on input
        def side_effect(*args, **kwargs):
            messages = kwargs.get('messages', [])
            if messages:
                user_input = messages[-1]["content"].lower()
                if "hello" in user_input or "hi" in user_input:
                    return create_mock_response("Hello! How can I assist you with your tasks today?")
                elif "add" in user_input and "task" in user_input:
                    return create_mock_response("Sure, I can help you add a task. What is the task you'd like to add?")
                elif "help" in user_input:
                    return create_mock_response("I can help you manage your tasks. You can ask me to add, list, complete, or delete tasks.")
            return create_mock_response("I understand. How else can I assist you?")
        
        mock_client.chat.completions.create.side_effect = side_effect
        
        # Test different inputs
        response1 = await agent.process_message(
            user_message="hello",
            conversation_history=[],
            user_id="test-user-id"
        )
        
        response2 = await agent.process_message(
            user_message="add task buy groceries",
            conversation_history=[],
            user_id="test-user-id"
        )
        
        response3 = await agent.process_message(
            user_message="help",
            conversation_history=[],
            user_id="test-user-id"
        )
        
        # Verify none of the responses match the static test response
        assert response1["content"] != "Hello! This is a test response from the chatbot. Your message was received."
        assert response2["content"] != "Hello! This is a test response from the chatbot. Your message was received."
        assert response3["content"] != "Hello! This is a test response from the chatbot. Your message was received."
        
        # Verify responses are contextually appropriate
        assert "hello" in response1["content"].lower()
        assert "add" in response2["content"].lower() or "task" in response2["content"].lower()
        assert "help" in response3["content"].lower()


@pytest.mark.asyncio
async def test_agent_processes_task_commands():
    """
    Test that the agent properly handles task-related commands.
    """
    config = AgentConfig()
    agent = TodoAgent(config=config)
    
    # Mock a response that would include tool calls for task operations
    mock_response = AsyncMock()
    mock_choice = AsyncMock()
    mock_message = AsyncMock()
    
    mock_message.content = "I've added the task 'Buy groceries' to your list."
    # Simulate a tool call for adding a task
    mock_tool_call = AsyncMock()
    mock_tool_call.id = "call_123"
    mock_tool_call.type = "function"
    mock_function = AsyncMock()
    mock_function.name = "add_task"
    mock_function.arguments = '{"title": "Buy groceries", "description": "Get milk, bread, and eggs"}'
    mock_tool_call.function = mock_function
    mock_message.tool_calls = [mock_tool_call]
    
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    
    with patch.object(agent, 'client') as mock_client:
        mock_client.chat.completions.create.return_value = mock_response
        
        # Also mock the tool execution to return a realistic result
        with patch.object(agent, '_execute_tool_call') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "task_id": "task_456",
                "message": "Task 'Buy groceries' added successfully",
                "task": {
                    "id": "task_456",
                    "title": "Buy groceries", 
                    "description": "Get milk, bread, and eggs",
                    "completed": False
                }
            }
            
            result = await agent.process_message(
                user_message="add task Buy groceries - get milk, bread, and eggs",
                conversation_history=[],
                user_id="test-user-id"
            )
            
            # Verify the response is not static
            assert result["content"] != "Hello! This is a test response from the chatbot. Your message was received."
            
            # Verify that tool calls were processed
            assert len(result.get("tool_calls", [])) > 0
            assert "Buy groceries" in result["content"]
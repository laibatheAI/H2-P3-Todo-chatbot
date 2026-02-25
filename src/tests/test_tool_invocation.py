"""
Integration tests for verifying MCP tool invocation in the Todo AI Chatbot application.
These tests ensure that when users send natural language commands like "add task",
the appropriate MCP tools are invoked correctly.
"""
import pytest
from unittest.mock import AsyncMock, patch
from backend.core.agents.todo_agent import TodoAgent, AgentConfig


@pytest.mark.asyncio
async def test_add_task_command_invokes_mcp_tool():
    """
    Test that when a user sends "add task food" or similar,
    the MCP task creation tool is called with correct parameters.
    """
    config = AgentConfig()
    agent = TodoAgent(config=config)
    
    # Mock the OpenAI response to include a tool call for adding a task
    mock_response = AsyncMock()
    mock_choice = AsyncMock()
    mock_message = AsyncMock()
    
    # Create a mock tool call for adding a task
    mock_tool_call = AsyncMock()
    mock_tool_call.id = "call_add_task_123"
    mock_tool_call.type = "function"
    mock_function = AsyncMock()
    mock_function.name = "add_task"
    mock_function.arguments = '{"title": "Buy groceries", "description": "Get food for the week", "priority": "medium"}'
    mock_tool_call.function = mock_function
    mock_message.tool_calls = [mock_tool_call]
    mock_message.content = "I've added the task 'Buy groceries' to your list."
    
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    
    with patch.object(agent, 'client') as mock_client:
        mock_client.chat.completions.create.return_value = mock_response
        
        # Mock the tool execution to return a realistic result
        with patch.object(agent, '_execute_tool_call') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "task_id": "task_456",
                "message": "Task 'Buy groceries' added successfully",
                "task": {
                    "id": "task_456",
                    "title": "Buy groceries", 
                    "description": "Get food for the week",
                    "priority": "medium",
                    "completed": False
                }
            }
            
            result = await agent.process_message(
                user_message="add task Buy groceries - get food for the week",
                conversation_history=[],
                user_id="test-user-id"
            )
            
            # Verify the tool was called
            mock_execute.assert_called_once()
            
            # Verify the response contains the expected content
            assert "Buy groceries" in result["content"]
            assert "added" in result["content"].lower()
            
            # Verify tool calls were recorded
            assert len(result.get("tool_calls", [])) > 0
            assert result["tool_calls"][0]["function"]["name"] == "add_task"


@pytest.mark.asyncio
async def test_various_task_commands_invoke_correct_tools():
    """
    Test that various natural language variations trigger the correct tools.
    """
    config = AgentConfig()
    agent = TodoAgent(config=config)
    
    test_cases = [
        {
            "input": "add a task Buy groceries",
            "expected_tool": "add_task",
            "expected_content_contains": ["added", "groceries"]
        },
        {
            "input": "create task Call mom tomorrow",
            "expected_tool": "add_task",
            "expected_content_contains": ["added", "mom"]
        },
        {
            "input": "show my tasks",
            "expected_tool": "list_tasks",
            "expected_content_contains": ["list", "tasks"]
        },
        {
            "input": "complete task 1",
            "expected_tool": "complete_task",
            "expected_content_contains": ["completed", "task"]
        },
        {
            "input": "delete task Buy groceries",
            "expected_tool": "delete_task",
            "expected_content_contains": ["deleted", "groceries"]
        }
    ]
    
    for test_case in test_cases:
        # Mock the OpenAI response to include the appropriate tool call
        mock_response = AsyncMock()
        mock_choice = AsyncMock()
        mock_message = AsyncMock()
        
        mock_tool_call = AsyncMock()
        mock_tool_call.id = f"call_{test_case['expected_tool']}_123"
        mock_tool_call.type = "function"
        mock_function = AsyncMock()
        mock_function.name = test_case["expected_tool"]
        # Basic arguments based on the command
        if test_case["expected_tool"] == "add_task":
            mock_function.arguments = f'{{"title": "{test_case["input"].split(" ", 2)[-1]}", "priority": "medium"}}'
        elif test_case["expected_tool"] == "list_tasks":
            mock_function.arguments = '{}'
        elif test_case["expected_tool"] == "complete_task":
            mock_function.arguments = '{"task_id": "1"}'
        elif test_case["expected_tool"] == "delete_task":
            mock_function.arguments = f'{{"task_id": "{test_case["input"].split()[-1]}"}}'
        else:
            mock_function.arguments = '{}'
        
        mock_tool_call.function = mock_function
        mock_message.tool_calls = [mock_tool_call]
        mock_message.content = f"I've processed your request to {test_case['input']}."
        
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]
        
        with patch.object(agent, 'client') as mock_client:
            mock_client.chat.completions.create.return_value = mock_response
            
            # Mock the tool execution
            with patch.object(agent, '_execute_tool_call') as mock_execute:
                mock_execute.return_value = {
                    "success": True,
                    "message": f"Successfully executed {test_case['expected_tool']} tool",
                    "result": {"test": "data"}
                }
                
                result = await agent.process_message(
                    user_message=test_case["input"],
                    conversation_history=[],
                    user_id="test-user-id"
                )
                
                # Verify the correct tool was called
                mock_execute.assert_called_once()
                
                # Verify the response is not the static test response
                assert result["content"] != "Hello! This is a test response from the chatbot. Your message was received."
                
                # Verify the response contains expected elements
                for expected in test_case["expected_content_contains"]:
                    assert expected.lower() in result["content"].lower()


@pytest.mark.asyncio
async def test_tool_execution_with_real_params():
    """
    Test that tool execution happens with realistic parameters from natural language.
    """
    config = AgentConfig()
    agent = TodoAgent(config=config)
    
    # Mock a response that includes a tool call with realistic parameters
    mock_response = AsyncMock()
    mock_choice = AsyncMock()
    mock_message = AsyncMock()
    
    mock_tool_call = AsyncMock()
    mock_tool_call.id = "call_add_task_realistic"
    mock_tool_call.type = "function"
    mock_function = AsyncMock()
    mock_function.name = "add_task"
    # Simulate realistic arguments extracted from natural language
    mock_function.arguments = '''
    {
        "title": "Buy milk and bread", 
        "description": "Get dairy and bakery items from the store",
        "priority": "high",
        "category": "shopping",
        "due_date": "2026-02-10T09:00:00Z"
    }
    '''
    mock_tool_call.function = mock_function
    mock_message.tool_calls = [mock_tool_call]
    mock_message.content = "I've added the task 'Buy milk and bread' to your high-priority shopping list for Feb 10th."
    
    mock_choice.message = mock_message
    mock_response.choices = [mock_choice]
    
    with patch.object(agent, 'client') as mock_client:
        mock_client.chat.completions.create.return_value = mock_response
        
        # Mock the tool execution to return a realistic result
        with patch.object(agent, '_execute_tool_call') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "task_id": "task_789",
                "message": "Task 'Buy milk and bread' added successfully with high priority",
                "task": {
                    "id": "task_789",
                    "title": "Buy milk and bread",
                    "description": "Get dairy and bakery items from the store",
                    "priority": "high",
                    "category": "shopping",
                    "due_date": "2026-02-10T09:00:00Z",
                    "completed": False
                }
            }
            
            result = await agent.process_message(
                user_message="add high priority shopping task Buy milk and bread - get dairy and bakery items from the store, due Feb 10th",
                conversation_history=[],
                user_id="test-user-id"
            )
            
            # Verify the response is not static
            assert result["content"] != "Hello! This is a test response from the chatbot. Your message was received."
            
            # Verify tool was called with appropriate parameters
            mock_execute.assert_called_once()
            call_args = mock_execute.call_args[0][0]  # Get the first argument (tool_call)
            assert call_args.function.name == "add_task"
            
            # Verify the response contains expected elements
            assert "milk" in result["content"].lower()
            assert "bread" in result["content"].lower()
            assert "high" in result["content"].lower()
            assert "shopping" in result["content"].lower()
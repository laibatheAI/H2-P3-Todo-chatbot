#!/usr/bin/env python3
"""
Simple test to verify that the agent is returning dynamic responses instead of static test responses.
"""
import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.core.agents.todo_agent import TodoAgent, AgentConfig


async def test_agent_response():
    """Test that the agent returns dynamic responses."""
    config = AgentConfig()
    agent = TodoAgent(config=config)
    
    # Test with a simple input
    result = await agent.process_message(
        user_message="hello",
        conversation_history=[],
        user_id="test-user-id"
    )
    
    print(f"Agent response: {result['content']}")
    
    # Check if it's the static test response
    if result["content"] == "Hello! This is a test response from the chatbot. Your message was received.":
        print("FAILED: Agent is still returning the static test response!")
        return False
    else:
        print("SUCCESS: Agent is returning a dynamic response!")
        return True


if __name__ == "__main__":
    success = asyncio.run(test_agent_response())
    sys.exit(0 if success else 1)
"""
Simple test to check if the chat endpoint is working.
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Test importing the chat agent
try:
    from backend.core.agents.chat_agent import get_default_agent
    print("[OK] Chat agent imported successfully")
    
    # Try to create an agent instance
    agent = get_default_agent()
    print("[OK] Chat agent created successfully")
except Exception as e:
    print(f"[ERROR] Error with chat agent: {e}")

# Test importing the tool executor
try:
    from backend.core.agents.tool_executor import execute_tool
    print("[OK] Tool executor imported successfully")
except Exception as e:
    print(f"[ERROR] Error with tool executor: {e}")

# Test importing the database session
try:
    from backend.src.database.database import get_session
    print("[OK] Database session imported successfully")
    
    # Try to get a session
    session_gen = get_session()
    session = next(session_gen)
    print("[OK] Database session created successfully")
    session.close()
except Exception as e:
    print(f"[ERROR] Error with database session: {e}")
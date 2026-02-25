"""
Test script for OpenAI function calling in the chat endpoint.

This script demonstrates how the chatbot handles task operations via function calling.
"""
import requests
import json

BASE_URL = "http://localhost:8000"
TOKEN = ""  # Set your auth token here after login
USER_ID = ""  # Set your user ID here


def test_chat_create_task():
    """Test creating a task via chat."""
    url = f"{BASE_URL}/api/v1/{USER_ID}/chat"
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "message": {
            "role": "user",
            "content": "Add a task 'Buy groceries'"
        }
    }
    
    print("📤 Sending: 'Add a task \"Buy groceries\"'")
    response = requests.post(url, json=payload, headers=headers)
    
    print(f"📥 Status: {response.status_code}")
    print(f"📥 Response: {json.dumps(response.json(), indent=2)}")
    return response.json()


def test_chat_complete_task():
    """Test completing a task via chat."""
    url = f"{BASE_URL}/api/v1/{USER_ID}/chat"
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "message": {
            "role": "user",
            "content": "Mark task 'Buy groceries' as complete"
        }
    }
    
    print("\n📤 Sending: 'Mark task \"Buy groceries\" as complete'")
    response = requests.post(url, json=payload, headers=headers)
    
    print(f"📥 Status: {response.status_code}")
    print(f"📥 Response: {json.dumps(response.json(), indent=2)}")
    return response.json()


def test_chat_list_tasks():
    """Test listing tasks via chat."""
    url = f"{BASE_URL}/api/v1/{USER_ID}/chat"
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "message": {
            "role": "user",
            "content": "Show me all my tasks"
        }
    }
    
    print("\n📤 Sending: 'Show me all my tasks'")
    response = requests.post(url, json=payload, headers=headers)
    
    print(f"📥 Status: {response.status_code}")
    print(f"📥 Response: {json.dumps(response.json(), indent=2)}")
    return response.json()


def test_chat_delete_task():
    """Test deleting a task via chat."""
    url = f"{BASE_URL}/api/v1/{USER_ID}/chat"
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "message": {
            "role": "user",
            "content": "Delete the task 'Buy groceries'"
        }
    }
    
    print("\n📤 Sending: 'Delete the task \"Buy groceries\"'")
    response = requests.post(url, json=payload, headers=headers)
    
    print(f"📥 Status: {response.status_code}")
    print(f"📥 Response: {json.dumps(response.json(), indent=2)}")
    return response.json()


if __name__ == "__main__":
    print("=" * 60)
    print("OpenAI Function Calling Test - Todo Chatbot")
    print("=" * 60)
    
    if not TOKEN:
        print("\n⚠️  Please set your auth TOKEN and USER_ID in this script")
        print("   You can get these by logging in via the /api/auth/login endpoint")
    else:
        # Run tests
        test_chat_create_task()
        test_chat_list_tasks()
        test_chat_complete_task()
        test_chat_delete_task()
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)

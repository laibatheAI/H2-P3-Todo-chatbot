"""
Test script to verify chat endpoint authentication and tool execution.

This script:
1. Logs in to get a JWT token
2. Calls the chat endpoint with the correct user_id
3. Verifies tool execution works properly
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000"


def login(email: str, password: str):
    """Login and get JWT token."""
    url = f"{BASE_URL}/api/auth/login"
    response = requests.post(url, json={"email": email, "password": password})
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        print(f"   Response: {response.text}")
        return None
    
    data = response.json()
    print(f"✅ Login successful")
    print(f"   User ID: {data['user']['id']}")
    print(f"   Token: {data['access_token'][:50]}...")
    
    return {
        "token": data["access_token"],
        "user_id": data["user"]["id"]
    }


def test_chat_create_task(token: str, user_id: str):
    """Test creating a task via chat."""
    url = f"{BASE_URL}/api/v1/{user_id}/chat"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "message": {
            "role": "user",
            "content": "Add a task 'Test task from chat'"
        }
    }
    
    print(f"\n📤 Testing: Create task via chat")
    print(f"   URL: {url}")
    response = requests.post(url, json=payload, headers=headers)
    
    print(f"📥 Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Success!")
        print(f"   Response: {data['response']['content']}")
        
        if data['response'].get('tool_calls'):
            print(f"   Tool calls: {len(data['response']['tool_calls'])}")
            for tc in data['response']['tool_calls']:
                print(f"      - {tc['function']['name']}")
        
        if data['response'].get('tool_results'):
            print(f"   Tool results:")
            for tr in data['response']['tool_results']:
                result = tr.get('result', {})
                if result.get('success'):
                    print(f"      ✅ {result.get('message', 'Success')}")
                else:
                    print(f"      ❌ {result.get('error', 'Unknown error')}")
    else:
        print(f"❌ Failed")
        try:
            error = response.json()
            print(f"   Error: {error.get('detail', error)}")
        except:
            print(f"   Error: {response.text}")
    
    return response


def test_chat_wrong_user_id(token: str, wrong_user_id: str):
    """Test chat with wrong user_id (should fail with 403)."""
    url = f"{BASE_URL}/api/v1/{wrong_user_id}/chat"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "message": {
            "role": "user",
            "content": "Hello"
        }
    }
    
    print(f"\n📤 Testing: Chat with WRONG user_id (should fail)")
    print(f"   URL: {url}")
    response = requests.post(url, json=payload, headers=headers)
    
    print(f"📥 Status: {response.status_code}")
    
    if response.status_code == 403:
        print(f"✅ Correctly rejected with 403 Forbidden")
        try:
            error = response.json()
            print(f"   Detail: {error.get('detail', 'Access denied')}")
        except:
            pass
    elif response.status_code == 200:
        print(f"❌ SECURITY ISSUE: Should have been rejected!")
    else:
        print(f"⚠️ Unexpected status: {response.status_code}")
    
    return response


def test_chat_missing_token(wrong_user_id: str):
    """Test chat without token (should fail with 401)."""
    url = f"{BASE_URL}/api/v1/{wrong_user_id}/chat"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "message": {
            "role": "user",
            "content": "Hello"
        }
    }
    
    print(f"\n📤 Testing: Chat without token (should fail with 401)")
    print(f"   URL: {url}")
    response = requests.post(url, json=payload, headers=headers)
    
    print(f"📥 Status: {response.status_code}")
    
    if response.status_code == 401:
        print(f"✅ Correctly rejected with 401 Unauthorized")
    else:
        print(f"⚠️ Unexpected status: {response.status_code}")
    
    return response


def main():
    print("=" * 70)
    print("Chat Endpoint Authentication Test")
    print("=" * 70)
    
    # Test credentials - use the user that exists in the database
    test_email = "test@test.com"
    test_password = "testpassword123"
    
    print(f"\n📝 Using test account: {test_email}")
    
    # Step 1: Login
    auth = login(test_email, test_password)
    if not auth:
        print("\n❌ Cannot proceed without valid authentication")
        print("   Make sure the test user exists in the database:")
        print(f"   Email: {test_email}")
        print(f"   Password: {test_password}")
        sys.exit(1)
    
    token = auth["token"]
    user_id = auth["user_id"]
    
    # Step 2: Test chat with correct user_id
    print("\n" + "=" * 70)
    print("Test 1: Chat with CORRECT user_id")
    print("=" * 70)
    test_chat_create_task(token, user_id)
    
    # Step 3: Test chat with wrong user_id
    print("\n" + "=" * 70)
    print("Test 2: Chat with WRONG user_id (Security Test)")
    print("=" * 70)
    wrong_id = "00000000-0000-0000-0000-000000000000"
    test_chat_wrong_user_id(token, wrong_id)
    
    # Step 4: Test chat without token
    print("\n" + "=" * 70)
    print("Test 3: Chat without token (Security Test)")
    print("=" * 70)
    test_chat_missing_token(wrong_id)
    
    print("\n" + "=" * 70)
    print("Test completed!")
    print("=" * 70)


if __name__ == "__main__":
    main()

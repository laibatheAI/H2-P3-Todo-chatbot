"""
Test script to verify OpenAI API key loading and chat functionality.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_api_key_loading():
    """Test that the API key is loaded correctly from src/.env"""
    print("=" * 70)
    print("Testing OpenAI API Key Loading")
    print("=" * 70)
    
    # Test 1: Check if src/.env exists
    src_env_path = project_root / "src" / ".env"
    print(f"\n1. Checking for src/.env file...")
    if src_env_path.exists():
        print(f"   [OK] Found: {src_env_path}")
    else:
        print(f"   [FAIL] Not found: {src_env_path}")
        return False
    
    # Test 2: Load and parse the .env file
    print(f"\n2. Loading OPENAI_API_KEY from src/.env...")
    from dotenv import dotenv_values
    env_vars = dotenv_values(src_env_path)
    
    api_key = env_vars.get("OPENAI_API_KEY", "").strip()
    
    if api_key:
        print(f"   [OK] API Key loaded successfully")
        print(f"   Key prefix: {api_key[:12]}...")
        print(f"   Key length: {len(api_key)} characters")
    else:
        print(f"   [FAIL] OPENAI_API_KEY not found in src/.env")
        return False
    
    # Test 3: Verify the key format (should start with sk-)
    print(f"\n3. Validating API key format...")
    if api_key.startswith("sk-"):
        print(f"   [OK] Valid OpenAI key format (starts with 'sk-')")
    else:
        print(f"   [WARN] Key format may be non-standard")
    
    # Test 4: Try to initialize OpenAI client
    print(f"\n4. Testing OpenAI client initialization...")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        print(f"   [OK] OpenAI client initialized successfully")
    except Exception as e:
        print(f"   [FAIL] Failed to initialize OpenAI client: {e}")
        return False
    
    # Test 5: Test the load_openai_api_key function from chat endpoint
    print(f"\n5. Testing load_openai_api_key() function...")
    try:
        from src.api.v1.endpoints.chat import load_openai_api_key, openai_client
        loaded_key = load_openai_api_key()
        
        if loaded_key:
            print(f"   [OK] load_openai_api_key() returned a key")
            print(f"   Key prefix: {loaded_key[:12]}...")
        else:
            print(f"   [FAIL] load_openai_api_key() returned empty string")
            return False
        
        if openai_client:
            print(f"   [OK] openai_client is initialized")
        else:
            print(f"   [FAIL] openai_client is None")
            return False
            
    except Exception as e:
        print(f"   [FAIL] Error testing load_openai_api_key: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("[SUCCESS] All API key loading tests passed!")
    print("=" * 70)
    return True


def test_chat_endpoint():
    """Test the chat endpoint with a simple request"""
    print("\n" + "=" * 70)
    print("Testing Chat Endpoint")
    print("=" * 70)
    
    import requests
    import json
    
    # First, login to get a token
    print("\n1. Logging in to get authentication token...")
    login_url = "http://localhost:8000/api/auth/login"
    login_data = {
        "email": "test@test.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(login_url, json=login_data)
        if response.status_code != 200:
            print(f"   [FAIL] Login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        login_result = response.json()
        token = login_result["access_token"]
        user_id = login_result["user"]["id"]
        print(f"   [OK] Login successful")
        print(f"   User ID: {user_id}")
    except Exception as e:
        print(f"   [FAIL] Login error: {e}")
        print(f"   Make sure the server is running on http://localhost:8000")
        return False
    
    # Test chat endpoint
    print("\n2. Sending chat request to create a task...")
    chat_url = f"http://localhost:8000/api/v1/{user_id}/chat"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "message": {
            "role": "user",
            "content": "Add a task 'Test task from API'"
        }
    }
    
    try:
        response = requests.post(chat_url, json=payload, headers=headers)
        print(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   [OK] Chat request successful")
            print(f"   Response: {result['response']['content'][:100]}...")
            
            if result['response'].get('tool_calls'):
                print(f"   Tool calls made: {len(result['response']['tool_calls'])}")
                for tc in result['response']['tool_calls']:
                    print(f"      - {tc['function']['name']}")
            
            if result['response'].get('tool_results'):
                print(f"   Tool results:")
                for tr in result['response']['tool_results']:
                    res = tr.get('result', {})
                    if res.get('success'):
                        print(f"      [OK] {res.get('message', 'Success')}")
                    else:
                        print(f"      [FAIL] {res.get('error', 'Unknown error')}")
            
            return True
        elif response.status_code == 503:
            print(f"   [FAIL] 503 Service Unavailable - OpenAI not configured")
            error_detail = response.json().get('detail', 'Unknown error')
            print(f"   Detail: {error_detail}")
            return False
        else:
            print(f"   [FAIL] Unexpected status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   [FAIL] Chat request error: {e}")
        return False


if __name__ == "__main__":
    print("\nOpenAI Configuration Test Suite\n")
    
    # Test API key loading
    api_key_ok = test_api_key_loading()
    
    if api_key_ok:
        # Test chat endpoint (requires running server)
        print("\nTo test the chat endpoint, make sure the server is running:")
        print("   python -m uvicorn src.main:app --reload --port 8000")
        print("\nWould you like to test the chat endpoint now? (y/n)")
        
        # Only run if server is running
        try:
            import requests
            requests.get("http://localhost:8000/api/health", timeout=2)
            test_chat_endpoint()
        except:
            print("\nServer not running. Skipping chat endpoint test.")
            print("   Start the server and run test_chat_auth.py for full testing.")
    else:
        print("\nAPI key loading failed. Please check src/.env file.")
        sys.exit(1)
    
    print("\nTest suite completed!")

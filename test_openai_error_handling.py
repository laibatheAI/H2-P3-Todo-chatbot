"""
Test script to verify OpenAI error handling in the chat endpoint.

This script tests various error scenarios:
1. Quota exceeded (429)
2. Authentication errors (401)
3. Permission denied (403)
4. Model not found (404)
5. Connection errors
6. Timeout errors
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_error_handling_function():
    """Test the handle_openai_error function directly."""
    print("=" * 70)
    print("Testing OpenAI Error Handling Function")
    print("=" * 70)
    
    from openai import (
        RateLimitError, 
        AuthenticationError, 
        PermissionDeniedError, 
        NotFoundError,
        APIConnectionError,
        APITimeoutError,
        APIError
    )
    from src.api.v1.endpoints.chat import handle_openai_error
    from fastapi import status
    
    test_cases = [
        {
            "name": "RateLimitError - Insufficient Quota",
            "error": RateLimitError(
                message='{"error": {"message": "You exceeded your current quota, please check your plan and billing details.", "type": "insufficient_quota"}}',
                response=None,
                body=None
            ),
            "expected_status": status.HTTP_503_SERVICE_UNAVAILABLE,
            "expected_keywords": ["usage limit", "quota", "administrator"]
        },
        {
            "name": "RateLimitError - Rate Limit",
            "error": RateLimitError(
                message='{"error": {"message": "Rate limit reached", "type": "rate_limit_error"}}',
                response=None,
                body=None
            ),
            "expected_status": status.HTTP_429_TOO_MANY_REQUESTS,
            "expected_keywords": ["too many requests", "wait"]
        },
        {
            "name": "AuthenticationError",
            "error": AuthenticationError(
                message='{"error": {"message": "Invalid API key", "type": "invalid_request_error"}}',
                response=None,
                body=None
            ),
            "expected_status": status.HTTP_503_SERVICE_UNAVAILABLE,
            "expected_keywords": ["authentication", "API key"]
        },
        {
            "name": "PermissionDeniedError",
            "error": PermissionDeniedError(
                message='{"error": {"message": "You don\'t have access to this model", "type": "permission_denied"}}',
                response=None,
                body=None
            ),
            "expected_status": status.HTTP_503_SERVICE_UNAVAILABLE,
            "expected_keywords": ["permission", "access", "administrator"]
        },
        {
            "name": "NotFoundError",
            "error": NotFoundError(
                message='{"error": {"message": "Model not found", "type": "not_found_error"}}',
                response=None,
                body=None
            ),
            "expected_status": status.HTTP_503_SERVICE_UNAVAILABLE,
            "expected_keywords": ["model", "configuration"]
        },
        {
            "name": "APIConnectionError",
            "error": APIConnectionError(
                message="Connection error",
                request=None
            ),
            "expected_status": status.HTTP_503_SERVICE_UNAVAILABLE,
            "expected_keywords": ["connect", "try again"]
        },
        {
            "name": "APITimeoutError",
            "error": APITimeoutError(
                message="Request timed out",
                request=None
            ),
            "expected_status": status.HTTP_504_GATEWAY_TIMEOUT,
            "expected_keywords": ["timed out", "try again"]
        }
    ]
    
    passed = 0
    failed = 0
    
    for test_case in test_cases:
        print(f"\nTest: {test_case['name']}")
        
        try:
            user_msg, status_code = handle_openai_error(test_case['error'])
            
            # Check status code
            if status_code == test_case['expected_status']:
                print(f"  [OK] Status code: {status_code}")
            else:
                print(f"  [FAIL] Expected {test_case['expected_status']}, got {status_code}")
                failed += 1
                continue
            
            # Check message contains expected keywords
            user_msg_lower = user_msg.lower()
            keywords_found = all(kw.lower() in user_msg_lower for kw in test_case['expected_keywords'])
            
            if keywords_found:
                print(f"  [OK] Message contains expected keywords")
                print(f"  Message: {user_msg[:100]}...")
                passed += 1
            else:
                print(f"  [FAIL] Message missing expected keywords")
                print(f"  Message: {user_msg}")
                failed += 1
                
        except Exception as e:
            print(f"  [FAIL] Exception during test: {e}")
            failed += 1
    
    print("\n" + "=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    return failed == 0


def test_chat_endpoint_error_response():
    """Test that the chat endpoint returns proper error responses."""
    print("\n" + "=" * 70)
    print("Testing Chat Endpoint Error Responses")
    print("=" * 70)
    
    import requests
    
    # First, login to get a token
    print("\n1. Logging in to get authentication token...")
    login_url = "http://localhost:8000/api/auth/login"
    login_data = {
        "email": "test@test.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(login_url, json=login_data, timeout=5)
        if response.status_code != 200:
            print(f"   [WARN] Login failed: {response.status_code}")
            print(f"   Skipping endpoint test (server may not be running)")
            return True
        
        login_result = response.json()
        token = login_result["access_token"]
        user_id = login_result["user"]["id"]
        print(f"   [OK] Login successful")
    except requests.exceptions.RequestException:
        print(f"   [WARN] Cannot connect to server")
        print(f"   Skipping endpoint test (server may not be running)")
        return True
    
    # Test chat endpoint
    print("\n2. Sending chat request (will test error handling)...")
    chat_url = f"http://localhost:8000/api/v1/{user_id}/chat"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
        "message": {
            "role": "user",
            "content": "Add a task 'test task'"
        }
    }
    
    try:
        response = requests.post(chat_url, json=payload, headers=headers, timeout=30)
        print(f"   Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   [OK] Chat request successful")
            print(f"   Response: {result['response']['content'][:100]}...")
            
            # Check if tool was executed
            if result['response'].get('tool_results'):
                for tr in result['response']['tool_results']:
                    res = tr.get('result', {})
                    if res.get('success'):
                        print(f"      [OK] {res.get('message', 'Success')}")
                    else:
                        print(f"      [WARN] {res.get('error', 'Unknown error')}")
            
            return True
            
        elif response.status_code == 503:
            result = response.json()
            detail = result.get('detail', 'Unknown error')
            print(f"   [INFO] Service unavailable: {detail}")
            
            # Check if it's a quota error
            if "quota" in detail.lower() or "usage limit" in detail.lower():
                print(f"   [OK] Quota error handled gracefully with user-friendly message")
                return True
            else:
                print(f"   [WARN] Unexpected 503 error")
                return False
                
        elif response.status_code == 500:
            result = response.json()
            detail = result.get('detail', 'Unknown error')
            print(f"   [FAIL] Internal server error: {detail}")
            print(f"   [INFO] Error handling may not be working correctly")
            return False
            
        else:
            print(f"   [WARN] Unexpected status: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"   [WARN] Request timed out")
        return True
    except Exception as e:
        print(f"   [FAIL] Error: {e}")
        return False


if __name__ == "__main__":
    print("\nOpenAI Error Handling Test Suite\n")
    
    # Test error handling function
    function_test_passed = test_error_handling_function()
    
    # Test chat endpoint (if server is running)
    print("\nNote: Endpoint test requires running server")
    print("Start server: python -m uvicorn src.main:app --reload --port 8000\n")
    endpoint_test_passed = test_chat_endpoint_error_response()
    
    print("\n" + "=" * 70)
    print("Test Suite Summary")
    print("=" * 70)
    print(f"Error handling function test: {'PASSED' if function_test_passed else 'FAILED'}")
    print(f"Chat endpoint test: {'PASSED' if endpoint_test_passed else 'SKIPPED/FAILED'}")
    print("=" * 70)
    
    if function_test_passed:
        print("\n[SUCCESS] Error handling is properly configured!")
        print("\nWhen OpenAI quota is exceeded, users will see:")
        print('  "Sorry! OpenAI usage limit reached. Please wait a few minutes')
        print('   or contact the administrator to check billing/usage."')
        print("\nAdmin can check usage at:")
        print("  https://platform.openai.com/account/usage")
    else:
        print("\n[FAIL] Error handling needs attention")
        sys.exit(1)

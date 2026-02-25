# OpenAI Error Handling Implementation

## Overview

This document describes the comprehensive error handling implementation for OpenAI API errors in the Todo AI Chatbot application.

## Problem Solved

**Before:** When OpenAI API quota was exceeded, users saw:
```
Error: Backend error: 500 - Error processing chat request: Error code: 429 - {...}
```

**After:** Users now see friendly, actionable messages:
```
Sorry! OpenAI usage limit reached. Please wait a few minutes or contact the administrator 
to check billing/usage. For more info: https://platform.openai.com/account/usage
```

## Implementation Details

### File Modified

**`src/api/v1/endpoints/chat.py`**

### Changes Made

#### 1. Import OpenAI Error Types

```python
from openai import (
    APIError, 
    RateLimitError, 
    AuthenticationError, 
    PermissionDeniedError, 
    NotFoundError, 
    APIConnectionError, 
    APITimeoutError
)
```

#### 2. Added Error Handler Function

```python
def handle_openai_error(error: Exception) -> tuple[str, int]:
    """
    Handle OpenAI API errors and return appropriate user-friendly messages.
    
    Returns:
        Tuple of (user_message, status_code)
    """
```

#### 3. Error Handling in Chat Endpoint

```python
except RateLimitError as e:
    user_msg, status_code = handle_openai_error(e)
    raise HTTPException(status_code=status_code, detail=user_msg)
```

## Error Types Handled

| Error Type | HTTP Status | User Message | Admin Action |
|------------|-------------|--------------|--------------|
| **RateLimitError (insufficient_quota)** | 503 | "Sorry! OpenAI usage limit reached. Please wait a few minutes or contact the administrator to check billing/usage." | Check usage at https://platform.openai.com/account/usage, upgrade plan |
| **RateLimitError (rate_limit)** | 429 | "Too many requests. Please wait a moment and try again." | Wait and retry, implement request throttling |
| **AuthenticationError** | 503 | "OpenAI authentication failed. Please contact the administrator to verify the API key configuration." | Verify API key in src/.env |
| **PermissionDeniedError** | 503 | "OpenAI API key doesn't have access to this model. Please contact the administrator." | Upgrade API key permissions or change model |
| **NotFoundError** | 503 | "OpenAI model configuration error. Please contact the administrator." | Check model name configuration |
| **APIConnectionError** | 503 | "Cannot connect to OpenAI service. Please try again in a few moments." | Check network, retry later |
| **APITimeoutError** | 504 | "OpenAI request timed out. Please try again." | Retry request, check network |
| **APIError (generic)** | 503 | "OpenAI service error. Please try again later." | Check OpenAI status page |
| **Unexpected errors** | 500 | "An unexpected error occurred. Please try again later." | Check logs for details |

## Backend Logging

All errors are logged with full details for debugging:

```
❌ OpenAI Error: Insufficient quota (429)
   Full error: {"error": {"message": "You exceeded your current quota...", ...}}
```

This allows administrators to:
- See the exact error from OpenAI
- Understand the root cause
- Take appropriate action

## Testing

### 1. Test Error Handling Function

```bash
cd E:\Q4-Hackathon\Hackathon2-phase3
python test_openai_error_handling.py
```

### 2. Test Chat Endpoint (with server running)

```bash
# Start server
python -m uvicorn src.main:app --reload --port 8000

# Run test
python test_openai_error_handling.py
```

### 3. Manual Testing

**Test quota error simulation:**
```bash
curl -X POST http://localhost:8000/api/v1/{user_id}/chat \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"message": {"role": "user", "content": "Add task test"}}'
```

Expected response when quota exceeded:
```json
{
  "detail": "Sorry! OpenAI usage limit reached. Please wait a few minutes or contact the administrator to check billing/usage. For more info: https://platform.openai.com/account/usage"
}
```

## Admin Instructions

### When Quota Error Occurs

1. **Check Usage Dashboard**
   - Visit: https://platform.openai.com/account/usage
   - Review current usage and limits

2. **Verify Billing**
   - Ensure payment method is valid
   - Check if billing threshold is reached

3. **Options**
   - Wait for quota to reset (next billing cycle)
   - Upgrade to higher tier plan
   - Use alternative API key with available quota

### When Other Errors Occur

| Error | Action |
|-------|--------|
| Authentication failed | Verify API key in `src/.env` |
| Permission denied | Check API key has access to configured model |
| Model not found | Verify model name is correct |
| Connection error | Check network connectivity |
| Timeout | Retry, check network latency |

## Code Structure

```
src/api/v1/endpoints/chat.py
├── handle_openai_error()        # Error handler function
├── load_openai_api_key()        # API key loading
├── get_system_prompt()          # System prompt
├── get_available_tools()        # Tool definitions
└── chat_endpoint()              # Main endpoint
    ├── Authentication check
    ├── OpenAI API call (with error handling)
    ├── Tool execution
    └── Response formatting
```

## Error Flow Diagram

```
User Request
    ↓
Chat Endpoint
    ↓
OpenAI API Call
    ↓
┌──────────────────────────────┐
│ Error Occurs?                │
├──────────────────────────────┤
│ YES → handle_openai_error()  │
│   ↓                          │
│ Log full error               │
│   ↓                          │
│ Return user-friendly message │
│   ↓                          │
│ HTTPException(status, msg)   │
└──────────────────────────────┘
    ↓
User sees friendly message
    ↓
Admin sees detailed logs
```

## Benefits

### For Users
- ✅ Clear, actionable error messages
- ✅ No raw API error codes
- ✅ Instructions on what to do next
- ✅ Better user experience

### For Administrators
- ✅ Detailed error logging
- ✅ Easy to diagnose issues
- ✅ Clear action items
- ✅ Reduced support burden

### For Developers
- ✅ Centralized error handling
- ✅ Easy to extend
- ✅ Consistent error responses
- ✅ Production-ready code

## Next Steps

1. **Monitor Usage**
   - Set up usage alerts in OpenAI dashboard
   - Track daily/weekly usage patterns

2. **Implement Rate Limiting**
   - Add request throttling per user
   - Prevent quota exhaustion

3. **Add Fallback Models**
   - Configure backup API keys
   - Switch models automatically on error

4. **Usage Dashboard**
   - Build admin UI for usage monitoring
   - Show quota consumption in real-time

## References

- OpenAI Error Codes: https://platform.openai.com/docs/guides/error-codes
- OpenAI Usage Dashboard: https://platform.openai.com/account/usage
- OpenAI Rate Limits: https://platform.openai.com/account/limits

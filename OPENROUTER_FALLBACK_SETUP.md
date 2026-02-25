# OpenRouter Fallback Setup Guide

## Overview

This implementation adds **OpenRouter** as a fallback AI provider when OpenAI quota is exceeded. The chatbot will automatically switch to OpenRouter (using Gemini model) when OpenAI returns quota errors.

## Architecture

```
User Request
    ↓
Try OpenAI (gpt-3.5-turbo)
    ↓
┌─────────────────────────────┐
│ OpenAI succeeds?            │
├─────────────────────────────┤
│ YES → Use OpenAI response   │
│ NO  → Check error type      │
│   ↓                         │
│   Quota/Model error?        │
│   ↓                         │
│   YES → Use OpenRouter      │
│   NO  → Return error        │
└─────────────────────────────┘
```

## Setup Instructions

### Step 1: Get OpenRouter API Key (FREE)

1. Go to **https://openrouter.ai/**
2. Sign up/Login with your account
3. Go to **Keys** section: https://openrouter.ai/keys
4. Click **"Create Key"**
5. Give it a name (e.g., "Todo Chatbot Fallback")
6. Copy the API key (starts with `sk-or-`)

### Step 2: Configure `.env`

Edit `src/.env` and add your OpenRouter API key:

```env
# Fallback AI Provider (OpenRouter with Gemini)
OPENROUTER_API_KEY = sk-or-YOUR-OPENROUTER-KEY-HERE
OPENROUTER_MODEL = google/gemini-2.0-flash-lite-preview-02-05
```

### Step 3: Restart Server

```bash
cd E:\Q4-Hackathon\Hackathon2-phase3
python -m uvicorn src.main:app --reload --port 8000
```

### Step 4: Test the Fallback

**Test 1: Normal operation (OpenAI works)**
```bash
curl -X POST http://localhost:8000/api/v1/{user_id}/chat \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"message": {"role": "user", "content": "Add task test"}}'
```

Expected: Uses OpenAI (logs show "Calling OpenAI model")

**Test 2: Simulate OpenAI failure**

Temporarily set invalid OpenAI key in `src/.env`:
```env
OPENAI_API_KEY = invalid-key
```

Restart server and send same request.

Expected: 
- Logs show "OpenAI failed, switching to OpenRouter fallback..."
- Logs show "Calling OpenRouter fallback model"
- Task still gets created successfully

## Available Models

### OpenRouter Free Models

These models are available for free on OpenRouter:

| Model | Name | Speed | Quality |
|-------|------|-------|---------|
| **Gemini 2.0 Flash Lite** | `google/gemini-2.0-flash-lite-preview-02-05` | Fast | Good |
| **Gemini 2.0 Flash** | `google/gemini-2.0-flash` | Fast | Good |
| **Llama 3.1 70B** | `meta-llama/llama-3.1-70b-instruct` | Medium | Very Good |
| **Qwen 2.5 72B** | `qwen/qwen-2.5-72b-instruct` | Medium | Very Good |

### Recommended Configuration

For **best free tier** experience:
```env
OPENROUTER_MODEL = google/gemini-2.0-flash-lite-preview-02-05
```

For **better quality** (may have rate limits):
```env
OPENROUTER_MODEL = google/gemini-2.0-flash
```

## How It Works

### 1. Primary Call (OpenAI)

```python
try:
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        tools=tools,
        ...
    )
except Exception as e:
    if should_use_fallback(e):
        # Switch to OpenRouter
        ...
```

### 2. Fallback Triggers

Fallback activates ONLY for:
- ✅ `insufficient_quota` (429)
- ✅ `model_not_found` (404)
- ✅ `permission_denied` for model access (403)

Fallback does NOT activate for:
- ❌ Invalid API key (authentication error)
- ❌ Network errors (different handling)
- ❌ Other unexpected errors

### 3. OpenRouter Call

```python
response = await call_openrouter_chat(
    messages=messages,
    tools=tools,
    tool_choice="auto"
)
```

Response is converted to OpenAI-compatible format.

### 4. Tool Execution

Tools execute **exactly the same way** regardless of which AI provider was used.

## Logging

### When OpenAI Works

```
🔥 CHAT ENDPOINT HIT
✅ Authenticated user: {user_id}
📞 Calling OpenAI model: gpt-3.5-turbo
✅ OpenAI response received
🔧 Executing tool: create_task
```

### When Fallback Activates

```
🔥 CHAT ENDPOINT HIT
✅ Authenticated user: {user_id}
📞 Calling OpenAI model: gpt-3.5-turbo
⚠️  OpenAI failed (RateLimitError), switching to OpenRouter fallback...
📞 Calling OpenRouter fallback model: google/gemini-2.0-flash-lite-preview-02-05
✅ OpenRouter response received
🔧 Executing tool: create_task
```

## Troubleshooting

### Issue: "OpenRouter API key not configured"

**Solution:** Ensure `OPENROUTER_API_KEY` is set in `src/.env`:
```env
OPENROUTER_API_KEY = sk-or-...
```

### Issue: "OpenRouter fallback also failed"

**Possible causes:**
1. Invalid API key
2. Network connectivity
3. Model not available

**Solution:**
- Verify API key at https://openrouter.ai/keys
- Check network connection
- Try different model (see Available Models above)

### Issue: Fallback not activating

**Check:**
1. Error type must be quota/model related
2. OpenRouter API key must be configured
3. Check logs for exact error message

## Cost Information

### OpenAI
- Paid service
- Pay per token
- Check pricing: https://openai.com/api/pricing/

### OpenRouter
- **Free tier available** for certain models
- Paid tier for premium models
- Check pricing: https://openrouter.ai/models

### Recommended: Free Tier Setup

Use **Gemini 2.0 Flash Lite** for fallback (free):
```env
OPENROUTER_MODEL = google/gemini-2.0-flash-lite-preview-02-05
```

This model is:
- ✅ Free on OpenRouter
- ✅ Fast response times
- ✅ Good quality for task management
- ✅ Supports tool calling

## Files Modified

| File | Purpose |
|------|---------|
| `src/services/openrouter_client.py` | NEW - OpenRouter client |
| `src/api/v1/endpoints/chat.py` | Updated with fallback logic |
| `src/.env` | Added OpenRouter configuration |

## Testing Checklist

- [ ] OpenRouter API key configured
- [ ] Server restarted after configuration
- [ ] Test with valid OpenAI key (should use OpenAI)
- [ ] Test with invalid OpenAI key (should use OpenRouter)
- [ ] Test task creation via chat
- [ ] Test task update via chat
- [ ] Test task deletion via chat
- [ ] Check logs for proper fallback messages

## Support

- OpenRouter Docs: https://openrouter.ai/docs
- OpenRouter Discord: https://discord.gg/openrouter
- OpenRouter Email: support@openrouter.ai

## Summary

✅ **Automatic fallback** when OpenAI quota exceeded
✅ **No code changes** needed in frontend
✅ **Same tool execution** logic
✅ **Free tier available** with OpenRouter
✅ **Production ready** error handling

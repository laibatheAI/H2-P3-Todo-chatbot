# 🚨 CRITICAL FIX: API Configuration for Vercel Deployment

## Problem Identified

Your Vercel environment variables have **THREE critical issues**:

1. ❌ **Typo in backend URL**: `https://laibatheuser-h2-p3-todochatbot.hf.spacea` (extra "a" at end)
2. ❌ **Duplicate API variables**: Both `NEXT_PUBLIC_API_BASE_URL` and `NEXT_PUBLIC_BACKEND_API_URL`
3. ❌ **Localhost in production**: `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000`

This is why login/signup are failing with `ERR_CONNECTION_REFUSED localhost:8000`.

---

## ✅ Solution: Fix Vercel Environment Variables

### Step 1: Go to Vercel Dashboard

1. Open: https://vercel.com/dashboard
2. Select your project
3. Click **Settings** tab
4. Click **Environment Variables** in sidebar

### Step 2: DELETE These Variables

Find and **DELETE** these variables:

| Variable | Action |
|----------|--------|
| `NEXT_PUBLIC_API_BASE_URL` | ❌ **DELETE** |
| `NEXT_PUBLIC_BACKEND_API_URL` (with typo) | ❌ **DELETE** |

### Step 3: ADD Correct Variable

Add **ONE** new variable:

| Key | Value | Environments |
|-----|-------|--------------|
| `NEXT_PUBLIC_BACKEND_API_URL` | `https://laibatheuser-h2-p3-todochatbot.hf.space` | ✅ Production ✅ Preview ✅ Development |

**⚠️ IMPORTANT**: Make sure the URL is **EXACTLY**:
```
https://laibatheuser-h2-p3-todochatbot.hf.space
```
- No extra "a" at the end
- No trailing slash
- HTTPS, not HTTP

### Step 4: Save and Redeploy

1. Click **Save** on the new variable
2. Go to **Deployments** tab
3. Find the latest deployment
4. Click the **⋮** (three dots) menu
5. Click **Redeploy**
6. ✅ **UNCHECK** "Use existing Build Cache"
7. Click **Redeploy**

---

## 🔧 Code Changes Applied

### Files Modified

| File | Change |
|------|--------|
| `src/lib/api-config.ts` | Updated comment with correct production URL |
| `next.config.js` | Removed `NEXT_PUBLIC_API_BASE_URL` reference |

### What Was Fixed

**Before (❌ Broken):**
```javascript
// next.config.js
env: {
  NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL, // ❌ Localhost!
}
```

**After (✅ Fixed):**
```javascript
// next.config.js
env: {
  NEXT_PUBLIC_BACKEND_API_URL: process.env.NEXT_PUBLIC_BACKEND_API_URL, // ✅ Production URL
}
```

---

## ✅ Verification Steps

### Before Redeploying

Run locally to test:

```bash
cd frontend

# Create .env.local with production URL (for testing)
echo "NEXT_PUBLIC_BACKEND_API_URL=https://laibatheuser-h2-p3-todochatbot.hf.space" > .env.local

# Build locally
npm run build

# If build succeeds, deployment should work
```

### After Redeploying

1. **Open your Vercel app URL**
2. **Open Browser DevTools** (F12)
3. **Go to Network tab**
4. **Try to register/login**
5. **Verify request URL shows:**
   ```
   ✅ https://laibatheuser-h2-p3-todochatbot.hf.space/api/auth/login
   ✅ https://laibatheuser-h2-p3-todochatbot.hf.space/api/auth/register
   ```
6. **NOT:**
   ```
   ❌ http://localhost:8000/api/auth/login
   ```

---

## 🚨 Common Mistakes to Avoid

### ❌ WRONG

```
NEXT_PUBLIC_BACKEND_API_URL=https://laibatheuser-h2-p3-todochatbot.hf.spacea
                                                              ^ extra "a"
```

### ✅ CORRECT

```
NEXT_PUBLIC_BACKEND_API_URL=https://laibatheuser-h2-p3-todochatbot.hf.space
```

### ❌ WRONG

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_BACKEND_API_URL=https://...
# Two variables = confusion!
```

### ✅ CORRECT

```
NEXT_PUBLIC_BACKEND_API_URL=https://laibatheuser-h2-p3-todochatbot.hf.space
# Only ONE variable
```

---

## 🔍 How to Verify Backend URL is Correct

Test the backend directly:

```bash
# In browser or terminal
curl https://laibatheuser-h2-p3-todochatbot.hf.space/api/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-02-26T...",
  "version": "1.0.0"
}
```

If this fails, the backend URL is wrong or backend is down.

---

## 📋 Complete Environment Variable Checklist

### Vercel Dashboard Settings

| Variable | Value | Required |
|----------|-------|----------|
| `NEXT_PUBLIC_BACKEND_API_URL` | `https://laibatheuser-h2-p3-todochatbot.hf.space` | ✅ Yes |
| `NEXT_PUBLIC_BETTER_AUTH_URL` | `https://h2-p3-todo-chatbot.vercel.app/api/auth` | Optional |

### Local Development (.env.local)

```env
# For local testing with local backend
NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000

# OR for local testing with production backend
NEXT_PUBLIC_BACKEND_API_URL=https://laibatheuser-h2-p3-todochatbot.hf.space
```

---

## 🐛 Troubleshooting

### Issue: Still seeing localhost requests after redeploy

**Solution:**
1. Verify you **deleted** `NEXT_PUBLIC_API_BASE_URL` from Vercel
2. Verify you **added** `NEXT_PUBLIC_BACKEND_API_URL` with correct URL
3. **Clear Vercel build cache** (uncheck "Use existing Build Cache")
4. Redeploy again

### Issue: Build fails with "NEXT_PUBLIC_BACKEND_API_URL is not set"

**Solution:**
1. Go to Vercel → Settings → Environment Variables
2. Verify variable exists
3. Verify it's set for **all environments** (Production, Preview, Development)
4. Redeploy

### Issue: Backend returns CORS error

**Solution:**
1. Backend must allow CORS for your Vercel domain
2. Backend should have: `allow_origins=["https://your-app.vercel.app"]`

---

## ✅ Final Checklist

Before marking as complete:

- [ ] Deleted `NEXT_PUBLIC_API_BASE_URL` from Vercel
- [ ] Deleted old `NEXT_PUBLIC_BACKEND_API_URL` (with typo)
- [ ] Added new `NEXT_PUBLIC_BACKEND_API_URL` with correct URL
- [ ] URL has NO trailing slash
- [ ] URL has NO extra "a" at end
- [ ] Variable set for all environments (Production, Preview, Development)
- [ ] Redeployed with build cache cleared
- [ ] Tested login in browser
- [ ] Verified Network tab shows correct backend URL
- [ ] No localhost requests in production

---

## 📞 Support

If issues persist after following these steps:

1. Check Vercel deployment logs for errors
2. Check browser console (F12) for exact error message
3. Verify backend is running: `https://laibatheuser-h2-p3-todochatbot.hf.space/api/health`
4. Verify no localhost references remain in code:
   ```bash
   grep -r "localhost:8000" frontend/src/ --exclude-dir=node_modules
   ```

---

**Last Updated:** 2026-02-26  
**Status:** ✅ Ready for deployment  
**Backend URL:** https://laibatheuser-h2-p3-todochatbot.hf.space

# Vercel Deployment Guide - Todo AI Chatbot Frontend

## 🚀 Quick Deployment Checklist

### ✅ Pre-Deployment

1. **Environment Variables in Vercel**
   - Go to Vercel Dashboard → Your Project → **Settings** → **Environment Variables**
   - Add the following variables:

   | Variable | Value | Environment |
   |----------|-------|-------------|
   | `NEXT_PUBLIC_BACKEND_API_URL` | `https://laibatheuser-h2-p3-todochatbot.hf.space` | Production, Preview, Development |

2. **Verify No Hardcoded URLs**
   - ✅ All API calls use `process.env.NEXT_PUBLIC_BACKEND_API_URL`
   - ✅ No `localhost:8000` in production code
   - ✅ Centralized API config in `src/lib/api-config.ts`

### ✅ During Deployment

1. **Trigger New Deployment**
   ```bash
   git add .
   git commit -m "Fix: Use environment variables for backend API URL"
   git push origin main
   ```

2. **Vercel Will Automatically Build**
   - Go to **Deployments** tab
   - Wait for build to complete (~2-3 minutes)

### ✅ Post-Deployment Testing

1. **Test Login/Signup**
   - Open your Vercel app URL
   - Try to register a new account
   - Try to login
   - Check browser console (F12) → Network tab
   - Verify requests go to: `https://laibatheuser-h2-p3-todochatbot.hf.space/api/auth/login`
   - **NOT** `http://localhost:8000`

2. **Test Tasks**
   - Create a new task
   - Mark task as complete
   - Delete a task
   - All requests should hit Hugging Face backend

---

## 🔧 Configuration Files

### New Files Created

1. **`src/lib/api-config.ts`** - Centralized API configuration
   ```typescript
   export const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL;
   ```

2. **`.env.local.example`** - Example environment file
   ```env
   NEXT_PUBLIC_BACKEND_API_URL=http://localhost:8000
   ```

### Modified Files

1. **`src/lib/api-client.ts`**
   - Now imports `API_BASE_URL` from config
   - No hardcoded localhost fallback

2. **`src/app/chat-interface.tsx`**
   - Uses `buildChatUrl()` from centralized config
   - No direct `process.env` access

---

## 🛠️ Troubleshooting

### Issue: Still seeing localhost requests

**Solution:**
1. Clear Vercel build cache:
   - Settings → Build & Development → **Clear Build Cache**
2. Redeploy without cache:
   - Deployments → Click latest → **Redeploy** → Uncheck "Use existing Build Cache"

### Issue: `NEXT_PUBLIC_BACKEND_API_URL is not set`

**Solution:**
1. Verify env variable is set in Vercel Dashboard
2. Variable name must be **exactly** `NEXT_PUBLIC_BACKEND_API_URL`
3. Redeploy after adding variable

### Issue: CORS errors in browser console

**Solution:**
1. Ensure backend has CORS configured for your Vercel domain
2. Backend should allow: `https://your-app.vercel.app`

---

## 📋 Environment Variables Reference

### Required Variables

| Name | Description | Example |
|------|-------------|---------|
| `NEXT_PUBLIC_BACKEND_API_URL` | Backend API base URL | `https://laibatheuser-h2-p3-todochatbot.hf.space` |

### How to Set in Vercel

1. Go to **Vercel Dashboard**
2. Select your project
3. Click **Settings** tab
4. Click **Environment Variables** in sidebar
5. Click **Add New**
6. Enter:
   - **Key**: `NEXT_PUBLIC_BACKEND_API_URL`
   - **Value**: `https://laibatheuser-h2-p3-todochatbot.hf.space`
   - **Environments**: ✅ Production ✅ Preview ✅ Development
7. Click **Save**

---

## 🔍 Code Changes Summary

### Before (❌ Broken in Production)

```typescript
// src/lib/api-client.ts
this.client = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
  // ❌ Hardcoded localhost fallback
});

// src/app/chat-interface.tsx
const backendUrl = process.env.NEXT_PUBLIC_BACKEND_API_URL;
const response = await fetch(`${backendUrl}/api/v1/${userId}/chat`, {
  // ❌ Direct env access, potential undefined
});
```

### After (✅ Production-Ready)

```typescript
// src/lib/api-config.ts
export const API_BASE_URL = getBackendUrl(); // Throws error if undefined in production

// src/lib/api-client.ts
this.client = axios.create({
  baseURL: API_BASE_URL, // ✅ Uses centralized config
});

// src/app/chat-interface.tsx
const { buildChatUrl } = await import('@/lib/api-config');
const chatUrl = buildChatUrl(userId); // ✅ Type-safe URL builder
const response = await fetch(chatUrl, { ... });
```

---

## ✅ Verification Commands

Run these before deploying:

```bash
# 1. Check for hardcoded localhost
grep -r "localhost:8000" frontend/src/ --exclude-dir=node_modules
# Should only show comments in api-config.ts

# 2. TypeScript check
cd frontend
npx tsc --noEmit
# Should show 0 errors

# 3. Build locally
npm run build
# Should complete successfully
```

---

## 🎯 Expected Network Requests

After deployment, browser Network tab should show:

```
✅ POST https://laibatheuser-h2-p3-todochatbot.hf.space/api/auth/login
✅ POST https://laibatheuser-h2-p3-todochatbot.hf.space/api/auth/register
✅ GET  https://laibatheuser-h2-p3-todochatbot.hf.space/api/tasks
✅ POST https://laibatheuser-h2-p3-todochatbot.hf.space/api/v1/{userId}/chat
```

**NOT:**
```
❌ POST http://localhost:8000/api/auth/login
```

---

## 🚨 Common Mistakes to Avoid

1. ❌ Committing `.env.local` to git (it's in `.gitignore` for a reason)
2. ❌ Using `process.env.NEXT_PUBLIC_BACKEND_API_URL` directly in components
3. ❌ Forgetting to set environment variable in Vercel
4. ❌ Not clearing build cache when changing env variables
5. ❌ Setting variable only for Production (set for all environments)

---

## 📞 Support

If issues persist:

1. Check Vercel deployment logs
2. Check browser console (F12)
3. Verify backend is running at Hugging Face
4. Test backend directly: `https://laibatheuser-h2-p3-todochatbot.hf.space/api/health`

---

**Last Updated:** 2026-02-26  
**Backend URL:** https://laibatheuser-h2-p3-todochatbot.hf.space  
**Frontend:** Next.js 14 + TypeScript on Vercel

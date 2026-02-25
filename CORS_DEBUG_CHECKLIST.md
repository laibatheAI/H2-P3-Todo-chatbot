# Debugging Checklist for FastAPI-Frontend Integration

## 1. Backend Server Verification
- [ ] Backend server is running on `http://localhost:8000`
- [ ] Run: `uvicorn src.main:app --reload`
- [ ] Visit `http://localhost:8000/docs` to verify API documentation is accessible
- [ ] Check that `/api/auth/login` and `/api/auth/register` endpoints appear in the docs

## 2. CORS Configuration Verification
- [ ] Verify CORS middleware is properly configured in `src/main.py`
- [ ] Check that `allow_origins` includes `http://localhost:3000`
- [ ] Confirm `allow_credentials=True`, `allow_methods=["*"]`, `allow_headers=["*"]`

## 3. Route Registration Verification
- [ ] Verify authentication routes are properly imported and included
- [ ] Check that `app.include_router(auth_router, prefix="/api", tags=["auth"])` is present
- [ ] Confirm routes are accessible at `/api/login`, `/api/register`, etc.

## 4. Module Import Verification
- [ ] Confirm all imports in `src/api/auth.py` are resolving correctly
- [ ] Check that `src/models/user.py`, `src/services/auth.py`, etc. exist and are accessible
- [ ] Verify no "No module named 'src.schemas'" errors appear in logs

## 5. Frontend API Call Verification
- [ ] Verify frontend is calling `http://localhost:8000/api/auth/login` (not `/api/login`)
- [ ] Check that frontend is sending credentials if required
- [ ] Confirm request headers are properly set (Content-Type: application/json)

## 6. Preflight Request Verification
- [ ] Use browser dev tools Network tab to check OPTIONS requests
- [ ] Verify OPTIONS requests to `/api/auth/login` return 200 status
- [ ] Confirm response headers include `Access-Control-Allow-Origin`

## 7. Manual Testing Steps
1. Start backend: `uvicorn src.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Visit frontend at `http://localhost:3000`
4. Try registering a new user
5. Check browser console for errors
6. Check backend terminal for incoming requests

## 8. Common Issues to Check
- [ ] Python path issues - ensure running from project root
- [ ] Missing dependencies - run `pip install` if needed
- [ ] Database connection issues - check database configuration
- [ ] Environment variables - ensure `.env` file is properly configured

## 9. Alternative Testing Methods
- Use curl to test endpoints directly:
  ```bash
  curl -X POST http://localhost:8000/api/register \
    -H "Content-Type: application/json" \
    -d '{"email":"test@example.com", "password":"password123", "name":"Test User"}'
  ```
- Use Postman or similar tools to test API endpoints independently

## 10. Production Considerations
- [ ] Update CORS origins for production environment
- [ ] Secure authentication tokens properly
- [ ] Implement proper error handling
- [ ] Add rate limiting for authentication endpoints
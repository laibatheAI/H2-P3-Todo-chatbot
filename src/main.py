import sys
import os
from pathlib import Path
from contextlib import asynccontextmanager

# Add the project root directory to Python path to enable absolute imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Depends, Path, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any
import time
import uuid
from datetime import datetime

from dotenv import load_dotenv
from src.database.init_db import create_db_and_tables

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    print("Initializing database tables...")
    create_db_and_tables()
    print("Database tables initialized successfully")
    yield
    # Cleanup on shutdown if needed
    print("Shutting down application")

app = FastAPI(
    title="Todo AI Chatbot API",
    description="Stateless Todo AI Chatbot with MCP tools integration",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware to allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev server
        "http://127.0.0.1:3000",
        "https://localhost:3000",
        "https://127.0.0.1:3000",
        # Add your production frontend URL here when deploying
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "Todo AI Chatbot"}

# Include routes here once they are created
try:
    # Import chat functionality from the local src structure
    from src.api.v1.endpoints.chat import router as chat_router
    app.include_router(chat_router, prefix="/api/v1", tags=["chat"])
    print("Chat router loaded successfully")
except ImportError as e:
    print(f"Chat router not available yet: {e}")

# Include authentication routes
try:
    from src.api.auth import router as auth_router
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
    print("Auth router loaded successfully")
except ImportError as e:
    print(f"Auth router not available yet: {e}")
    # Define fallback auth routes if the router fails to load
    @app.post("/api/auth/login")
    async def login_fallback():
        raise HTTPException(status_code=500, detail="Authentication service not available")
    
    @app.post("/api/auth/register") 
    async def register_fallback():
        raise HTTPException(status_code=500, detail="Authentication service not available")

# Include task routes
try:
    from src.api.tasks import router as tasks_router
    app.include_router(tasks_router, tags=["tasks"])
    print("Tasks router loaded successfully")
except ImportError as e:
    print(f"Tasks router not available yet: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

"""
NEXUS — Autonomous AI Agent Platform
Backend Entry Point

Responsibilities:
- App initialization
- Middleware registration  
- Router mounting
- DB + Redis startup via lifespan

NOT responsible for: agent logic, tool execution, task business logic
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import tasks, ws
from services.memory import init_db, init_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize all external connections on startup."""
    await init_db()
    await init_redis()
    yield
    # Teardown goes here if needed


app = FastAPI(
    title="NEXUS Agent API",
    version="0.2.0",
    description="Autonomous AI Agent Platform — Backend API",
    lifespan=lifespan,
)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(ws.router, prefix="/ws", tags=["websocket"])


@app.get("/health")
async def health_check() -> dict:
    return {"success": True, "data": {"status": "ok", "version": "0.2.0"}, "error": None}
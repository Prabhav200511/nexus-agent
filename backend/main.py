from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import tasks, ws

app = FastAPI(title="NEXUS Autonomous Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    return {
        "success": True,
        "data": "NEXUS backend running",
        "error": None
    }

app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(ws.router, prefix="/ws", tags=["websocket"])
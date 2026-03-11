from fastapi import APIRouter
from pydantic import BaseModel
from uuid import uuid4

router = APIRouter()

TASK_STORE = {}

class TaskCreate(BaseModel):
    prompt: str


@router.post("/")
async def create_task(task: TaskCreate):
    task_id = str(uuid4())

    TASK_STORE[task_id] = {
        "id": task_id,
        "prompt": task.prompt,
        "status": "created"
    }

    return {
        "success": True,
        "data": TASK_STORE[task_id],
        "error": None
    }


@router.get("/{task_id}")
async def get_task(task_id: str):
    task = TASK_STORE.get(task_id)

    if not task:
        return {
            "success": False,
            "data": None,
            "error": "Task not found"
        }

    return {
        "success": True,
        "data": task,
        "error": None
    }
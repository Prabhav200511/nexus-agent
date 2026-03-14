"""
Tasks Router — HTTP layer only.

Responsibilities:
  - Parse and validate incoming HTTP requests
  - Persist tasks via memory service
  - Trigger agent via executor (fire-and-forget background task)
  - Return HTTP responses

NOT allowed here:
  - LLM calls
  - Tool execution (no browser, search, firecrawl)
  - LangGraph imports
  - Business logic beyond routing

The wall between HTTP and agent is enforced by only importing from:
  - models/      (data shapes)
  - services/    (DB/Redis access)
  - agent/executor.py  (one clean entry point to the agent world)
"""

from uuid import UUID
from fastapi import APIRouter, HTTPException, BackgroundTasks

from models.task import Task, TaskCreate, TaskApproval, TaskStatus
from services.memory import save_task, get_task, list_tasks, update_task_status
from agent.executor import run_agent_task, resume_agent_task

router = APIRouter()


@router.post("/", response_model=dict)
async def create_task(payload: TaskCreate, background_tasks: BackgroundTasks) -> dict:
    """
    Create a new task and start the agent in the background.
    Returns task_id immediately — client subscribes via WebSocket for live updates.
    """
    task = Task(prompt=payload.prompt)
    await save_task(task)

    # Hand off to executor — this is the ONLY place the agent is triggered from HTTP land
    background_tasks.add_task(run_agent_task, task.id)

    return {"success": True, "data": {"task_id": str(task.id)}, "error": None}


@router.get("/", response_model=dict)
async def list_all_tasks() -> dict:
    tasks = await list_tasks()
    return {
        "success": True,
        "data": [t.model_dump(mode="json") for t in tasks],
        "error": None,
    }


@router.get("/{task_id}", response_model=dict)
async def get_task_by_id(task_id: UUID) -> dict:
    task = await get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"success": True, "data": task.model_dump(mode="json"), "error": None}


@router.post("/{task_id}/approve", response_model=dict)
async def approve_task_action(
    task_id: UUID,
    payload: TaskApproval,
    background_tasks: BackgroundTasks,
) -> dict:
    """
    Human-in-the-loop: approve or reject a paused agent action.
    The agent graph is resumed via executor — never directly from this router.
    """
    task = await get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status != TaskStatus.AWAITING_APPROVAL:
        raise HTTPException(status_code=400, detail="Task is not awaiting approval")

    new_status = TaskStatus.RUNNING if payload.approved else TaskStatus.FAILED
    await update_task_status(task_id, new_status)

    if payload.approved:
        # Resume the paused LangGraph checkpoint — again via executor only
        background_tasks.add_task(resume_agent_task, task_id)

    return {
        "success": True,
        "data": {"approved": payload.approved, "task_id": str(task_id)},
        "error": None,
    }
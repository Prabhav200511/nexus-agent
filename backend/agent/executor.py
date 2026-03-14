"""
Agent Executor — The single bridge between HTTP world and agent world.

Responsibilities:
  - Start a new agent run for a task
  - Resume a paused agent run after human approval
  - Persist state changes to DB after each step
  - Broadcast live updates to WebSocket clients

This is the ONLY module that:
  - Imports from agent/graph.py
  - Imports from routers/ws.py (for broadcasting)
  - Is called by routers/tasks.py

The strict import chain:
  routers/tasks.py
      → agent/executor.py      (this file)
          → agent/graph.py     (LangGraph orchestration)
              → agent/tools.py (tool execution)
              → services/llm.py (LLM calls)
          → services/memory.py (persistence)
          → routers/ws.py      (broadcasting — import only manager)

Nothing flows in reverse. Routers never touch graph.py or tools.py directly.
"""

from uuid import UUID

from models.task import Task, TaskStatus, StepStatus
from services.memory import get_task, update_task, update_task_status
from agent.graph import agent_graph


async def _broadcast(task_id: str, event: str, data: dict) -> None:
    """Push a live update to all WebSocket clients watching this task."""
    # Late import to avoid circular dependency
    from routers.ws import manager
    await manager.broadcast(task_id, {"event": event, "task_id": task_id, **data})


async def run_agent_task(task_id: UUID) -> None:
    """
    Start a fresh agent run.
    Called as a FastAPI background task from routers/tasks.py.
    """
    task = await get_task(task_id)
    if not task:
        return

    task_id_str = str(task_id)
    config = {"configurable": {"thread_id": task_id_str}}

    initial_state = {
        "task_id": task_id_str,
        "prompt": task.prompt,
        "steps": [],
        "current_step_index": 0,
        "status": "running",
        "result": "",
        "error": "",
        "awaiting_approval": False,
        "approval_granted": False,
    }

    await update_task_status(task_id, TaskStatus.RUNNING)
    await _broadcast(task_id_str, "task_started", {"prompt": task.prompt})

    try:
        async for state in agent_graph.astream(initial_state, config=config):
            # Each streamed state update = one node completed
            await _sync_state_to_db(task_id, state)
            await _broadcast(task_id_str, "step_update", {
                "status": state.get("status", "running"),
                "steps": [_serialize_step(s) for s in state.get("steps", [])],
                "current_step_index": state.get("current_step_index", 0),
            })

            # Graph paused for human approval
            if state.get("status") == "awaiting_approval":
                await update_task_status(task_id, TaskStatus.AWAITING_APPROVAL)
                await _broadcast(task_id_str, "awaiting_approval", {
                    "message": "Agent is paused. Approve to continue.",
                })
                return  # Stop here — resumed by resume_agent_task()

        # Graph completed
        final = await get_task(task_id)
        await update_task_status(task_id, TaskStatus.DONE)
        await _broadcast(task_id_str, "task_done", {
            "result": state.get("result", ""),
        })

    except Exception as e:
        await update_task_status(task_id, TaskStatus.FAILED)
        await _broadcast(task_id_str, "task_failed", {"error": str(e)})


async def resume_agent_task(task_id: UUID) -> None:
    """
    Resume a paused agent after human approval.
    Called as a FastAPI background task from routers/tasks.py POST /{id}/approve.
    """
    task_id_str = str(task_id)
    config = {
        "configurable": {
            "thread_id": task_id_str,
        }
    }

    await update_task_status(task_id, TaskStatus.RUNNING)
    await _broadcast(task_id_str, "task_resumed", {"message": "Approval granted. Continuing..."})

    try:
        # Resume from the LangGraph checkpoint (MemorySaver holds the state)
        async for state in agent_graph.astream(None, config=config):
            await _sync_state_to_db(task_id, state)
            await _broadcast(task_id_str, "step_update", {
                "status": state.get("status", "running"),
                "steps": [_serialize_step(s) for s in state.get("steps", [])],
                "current_step_index": state.get("current_step_index", 0),
            })

        await update_task_status(task_id, TaskStatus.DONE)
        await _broadcast(task_id_str, "task_done", {"result": state.get("result", "")})

    except Exception as e:
        await update_task_status(task_id, TaskStatus.FAILED)
        await _broadcast(task_id_str, "task_failed", {"error": str(e)})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _sync_state_to_db(task_id: UUID, state: dict) -> None:
    """Persist the latest graph state snapshot to Postgres."""
    task = await get_task(task_id)
    if not task:
        return
    task.steps = state.get("steps", task.steps)
    task.result = state.get("result") or task.result
    task.error = state.get("error") or task.error
    await update_task(task)


def _serialize_step(step) -> dict:
    if hasattr(step, "model_dump"):
        return step.model_dump(mode="json")
    return step
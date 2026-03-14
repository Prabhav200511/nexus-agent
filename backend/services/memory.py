"""
Memory Service — All DB and Redis interactions live here.

Responsibilities:
  - PostgreSQL: persist tasks and steps
  - Redis: short-term cache, agent state between checkpoints

NOT allowed here:
  - Agent logic
  - LLM calls
  - Tool execution
  - HTTP handling

All other modules access persistence ONLY through this service.
"""

import os
import json
from uuid import UUID
from datetime import datetime

import asyncpg
import redis.asyncio as aioredis

from models.task import Task, TaskStatus

# --- Connection globals (initialized on startup) ---
_pg_pool: asyncpg.Pool | None = None
_redis: aioredis.Redis | None = None


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

async def init_db() -> None:
    global _pg_pool
    dsn = os.getenv("DATABASE_URL", "postgresql://nexus:nexus@localhost:5432/nexus")
    _pg_pool = await asyncpg.create_pool(dsn)
    await _ensure_schema()
    print("[memory] PostgreSQL connected")


async def init_redis() -> None:
    global _redis
    url = os.getenv("REDIS_URL", "redis://localhost:6379")
    _redis = aioredis.from_url(url, decode_responses=True)
    print("[memory] Redis connected")


async def _ensure_schema() -> None:
    """Create tables if they don't exist yet."""
    async with _pg_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id          UUID PRIMARY KEY,
                prompt      TEXT NOT NULL,
                status      TEXT NOT NULL DEFAULT 'pending',
                steps       JSONB NOT NULL DEFAULT '[]',
                result      TEXT,
                error       TEXT,
                created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """)


# ---------------------------------------------------------------------------
# Task persistence (Postgres)
# ---------------------------------------------------------------------------

async def save_task(task: Task) -> None:
    async with _pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO tasks (id, prompt, status, steps, result, error, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            task.id,
            task.prompt,
            task.status.value,
            json.dumps([s.model_dump(mode="json") for s in task.steps]),
            task.result,
            task.error,
            task.created_at,
            task.updated_at,
        )


async def get_task(task_id: UUID) -> Task | None:
    async with _pg_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM tasks WHERE id = $1", task_id)
    if not row:
        return None
    return _row_to_task(row)


async def list_tasks() -> list[Task]:
    async with _pg_pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM tasks ORDER BY created_at DESC")
    return [_row_to_task(r) for r in rows]


async def update_task_status(task_id: UUID, status: TaskStatus) -> None:
    async with _pg_pool.acquire() as conn:
        await conn.execute(
            "UPDATE tasks SET status = $1, updated_at = $2 WHERE id = $3",
            status.value,
            datetime.utcnow(),
            task_id,
        )


async def update_task(task: Task) -> None:
    """Full task update — called by executor after each step."""
    async with _pg_pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE tasks
            SET status = $1, steps = $2, result = $3, error = $4, updated_at = $5
            WHERE id = $6
            """,
            task.status.value,
            json.dumps([s.model_dump(mode="json") for s in task.steps]),
            task.result,
            task.error,
            datetime.utcnow(),
            task.id,
        )


def _row_to_task(row: asyncpg.Record) -> Task:
    from models.task import Step
    steps_raw = json.loads(row["steps"]) if isinstance(row["steps"], str) else row["steps"]
    return Task(
        id=row["id"],
        prompt=row["prompt"],
        status=TaskStatus(row["status"]),
        steps=[Step(**s) for s in steps_raw],
        result=row["result"],
        error=row["error"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


# ---------------------------------------------------------------------------
# Redis helpers (short-term agent memory)
# ---------------------------------------------------------------------------

async def cache_set(key: str, value: str, ttl_seconds: int = 3600) -> None:
    await _redis.set(key, value, ex=ttl_seconds)


async def cache_get(key: str) -> str | None:
    return await _redis.get(key)


async def cache_delete(key: str) -> None:
    await _redis.delete(key)
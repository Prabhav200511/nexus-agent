"""
Task Model — Data definitions only.
No agent logic. No tool calls. No DB queries.
Pure schema: what a Task looks like in memory and over the wire.
"""

from enum import Enum
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    DONE = "done"
    FAILED = "failed"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class Step(BaseModel):
    """A single execution step produced by the agent."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: str = ""
    status: StepStatus = StepStatus.PENDING
    tool_used: str | None = None
    output: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = None


class Task(BaseModel):
    """A full agent task — persisted to Postgres via memory service."""
    id: UUID = Field(default_factory=uuid4)
    prompt: str
    status: TaskStatus = TaskStatus.PENDING
    steps: list[Step] = []
    result: str | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TaskCreate(BaseModel):
    prompt: str


class TaskApproval(BaseModel):
    approved: bool
    reason: str | None = None
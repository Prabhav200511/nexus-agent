"""
Agent Graph — LangGraph workflow definition.

Responsibilities:
  - Define the agent's state machine (nodes + edges)
  - Decide WHICH tool to call next (routing logic)
  - Implement the human-in-the-loop interrupt checkpoint
  - Invoke tools via dispatch_tool() — never directly

NOT allowed here:
  - Implementing tool logic (no httpx, no playwright, no browser-use)
  - DB/Redis access
  - HTTP/WebSocket handling
  - LLM calls (delegated to services/llm.py)

Architecture enforced:
  graph.py → dispatch_tool() → tools.py → external services
  graph.py → llm.py          → LiteLLM  → LLM providers
"""

from __future__ import annotations

from typing import TypedDict, Annotated
from uuid import UUID

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from models.task import Step, StepStatus, TaskStatus
from agent.tools import dispatch_tool, ToolResult
from services.llm import chat


# ---------------------------------------------------------------------------
# Agent State — what flows through the graph
# ---------------------------------------------------------------------------

class AgentState(TypedDict):
    task_id: str
    prompt: str
    steps: list[Step]
    current_step_index: int
    status: str
    result: str
    error: str
    awaiting_approval: bool
    approval_granted: bool


# ---------------------------------------------------------------------------
# Nodes — each node has ONE job
# ---------------------------------------------------------------------------

async def node_plan(state: AgentState) -> AgentState:
    """
    Planning node: decompose the prompt into steps.
    Imports planner here to keep graph.py from having planning logic inline.
    """
    from agent.planner import decompose_task
    steps = await decompose_task(state["prompt"])
    return {**state, "steps": steps, "current_step_index": 0, "status": "running"}


async def node_execute_step(state: AgentState) -> AgentState:
    """
    Execution node: run the current step's tool via dispatch_tool().
    Does NOT implement any tool logic — purely orchestrates.
    """
    idx = state["current_step_index"]
    steps = list(state["steps"])

    if idx >= len(steps):
        return {**state, "status": "done"}

    step = steps[idx]
    step.status = StepStatus.RUNNING

    # Dispatch to tools.py — this is the ONLY place tools are called
    result: ToolResult = await dispatch_tool(step.tool_used or "web_search", step.description)

    step.status = StepStatus.DONE if result.success else StepStatus.FAILED
    step.output = result.output
    steps[idx] = step

    return {
        **state,
        "steps": steps,
        "current_step_index": idx + 1,
        "error": result.error or state.get("error", ""),
    }


async def node_check_approval(state: AgentState) -> AgentState:
    """
    Human-in-the-loop node: pause before sensitive actions (email, bookings).
    Sets awaiting_approval=True — LangGraph interrupt fires here.
    """
    idx = state["current_step_index"]
    steps = state["steps"]

    if idx < len(steps):
        next_tool = steps[idx].tool_used or ""
        sensitive_tools = {"gmail", "drive", "slack", "browser"}
        if next_tool in sensitive_tools:
            return {**state, "awaiting_approval": True, "status": "awaiting_approval"}

    return {**state, "awaiting_approval": False}


async def node_summarize(state: AgentState) -> AgentState:
    """Summarize all step outputs into a final result string."""
    outputs = [
        f"Step {i+1} ({s.tool_used}): {s.output or 'no output'}"
        for i, s in enumerate(state["steps"])
    ]
    summary_prompt = (
        f"Task: {state['prompt']}\n\n"
        f"Execution results:\n" + "\n".join(outputs) + "\n\n"
        "Provide a concise final summary for the user."
    )
    result = await chat([{"role": "user", "content": summary_prompt}])
    return {**state, "result": result, "status": "done"}


# ---------------------------------------------------------------------------
# Routing — decides which node comes next
# ---------------------------------------------------------------------------

def route_after_approval_check(state: AgentState) -> str:
    if state.get("awaiting_approval"):
        return "await_human"   # LangGraph interrupt node
    return "execute_step"


def route_after_execution(state: AgentState) -> str:
    idx = state["current_step_index"]
    steps = state["steps"]

    if idx >= len(steps):
        return "summarize"

    # Check if any step failed fatally
    last_step = steps[idx - 1] if idx > 0 else None
    if last_step and last_step.status == StepStatus.FAILED:
        return "summarize"  # Summarize what we have

    return "check_approval"


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_graph() -> StateGraph:
    checkpointer = MemorySaver()  # Swap for RedisCheckpointer in production
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("plan", node_plan)
    graph.add_node("check_approval", node_check_approval)
    graph.add_node("execute_step", node_execute_step)
    graph.add_node("summarize", node_summarize)

    # Entry point
    graph.set_entry_point("plan")

    # Edges
    graph.add_edge("plan", "check_approval")
    graph.add_conditional_edges("check_approval", route_after_approval_check, {
        "await_human": END,       # Graph pauses here — resumed by executor on approval
        "execute_step": "execute_step",
    })
    graph.add_conditional_edges("execute_step", route_after_execution, {
        "check_approval": "check_approval",
        "summarize": "summarize",
    })
    graph.add_edge("summarize", END)

    return graph.compile(checkpointer=checkpointer)


# Compiled graph — imported by executor.py only
agent_graph = build_graph()
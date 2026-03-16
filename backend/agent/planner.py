"""
Agent Planner — Task decomposition ONLY.

Responsibilities:
  - Call LLM to break a prompt into structured steps
  - Parse LLM output into Step objects
  - Return a list of steps with assigned tools

NOT allowed here:
  - Executing any tool (no browser, search, firecrawl)
  - DB/Redis access
  - HTTP handling
  - WebSocket communication
  - LangGraph graph definitions

The planner THINKS. It does not ACT.
"""

import re
from models.task import Step, StepStatus
from services.llm import plan as llm_plan

# Maps keywords in the plan to canonical tool names
TOOL_KEYWORD_MAP = {
    "web_search": "web_search",
    "search": "web_search",
    "browser": "browser",
    "browse": "browser",
    "navigate": "browser",
    "firecrawl": "firecrawl",
    "extract": "firecrawl",
    "scrape": "firecrawl",
    "gmail": "gmail",
    "email": "gmail",
    "drive": "drive",
    "slack": "slack",
    "done": "done",
    "summarize": "done",
    "finish": "done",
}


def _detect_tool(step_text: str) -> str:
    """Detect which tool a plan step refers to."""
    lower = step_text.lower()
    for keyword, tool in TOOL_KEYWORD_MAP.items():
        if keyword in lower:
            return tool
    return "web_search"  # Default fallback


def _parse_plan(raw_plan: str) -> list[dict]:
    """
    Parse a numbered LLM plan into a list of {name, description, tool}.
    Handles formats like:
      1. Do something [tool: browser]
      1) Do something
      Step 1: Do something
    """
    steps = []
    lines = [l.strip() for l in raw_plan.strip().splitlines() if l.strip()]

    for line in lines:
        # Strip leading number/bullet
        cleaned = re.sub(r"^(\d+[\.\)]\s*|Step\s+\d+:\s*)", "", line, flags=re.IGNORECASE)
        if not cleaned:
            continue

        tool = _detect_tool(cleaned)

        # Use first ~60 chars as name, full line as description
        name = cleaned[:60].rstrip(",. ") if len(cleaned) > 60 else cleaned
        steps.append({"name": name, "description": cleaned, "tool": tool})

    return steps


async def decompose_task(prompt: str) -> list[Step]:
    """
    Main entry point for the planner.
    Calls LLM → parses output → returns Step objects ready for the executor.
    """
    raw_plan = await llm_plan(prompt)
    parsed = _parse_plan(raw_plan)

    return [
        Step(
            name=item["name"],
            description=item["description"],
            tool_used=item["tool"],
            status=StepStatus.PENDING,
        )
        for item in parsed
    ]
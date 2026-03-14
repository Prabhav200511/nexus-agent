"""
LLM Service — Unified LLM interface via LiteLLM.

Responsibilities:
  - Wrap LiteLLM calls with consistent error handling
  - Manage model selection and fallback
  - Expose clean async functions for the agent layer

NOT allowed here:
  - Tool execution
  - Task persistence
  - HTTP handling
  - LangGraph graph definitions
"""

import os
from litellm import acompletion
from litellm.types.utils import ModelResponse


PRIMARY_MODEL = os.getenv("PRIMARY_MODEL", "gpt-4o")
FALLBACK_MODEL = os.getenv("FALLBACK_MODEL", "claude-opus-4-6")
MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))


async def chat(
    messages: list[dict],
    model: str = PRIMARY_MODEL,
    temperature: float = 0.2,
    max_tokens: int = MAX_TOKENS,
) -> str:
    """
    Send a chat completion request and return the assistant's text reply.
    Automatically falls back to FALLBACK_MODEL on failure.
    """
    try:
        response: ModelResponse = await acompletion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content or ""

    except Exception as primary_error:
        if model == PRIMARY_MODEL:
            print(f"[llm] Primary model failed ({primary_error}), falling back to {FALLBACK_MODEL}")
            return await chat(messages, model=FALLBACK_MODEL, temperature=temperature)
        raise primary_error


async def plan(task_prompt: str) -> str:
    """
    Ask the LLM to decompose a task into a numbered execution plan.
    Returns raw text — parsing is handled by agent/planner.py.
    """
    system = (
        "You are a task planning assistant for an autonomous AI agent. "
        "Given a user task, produce a numbered step-by-step execution plan. "
        "Each step must specify: what to do and which tool to use "
        "(web_search | browser | firecrawl | gmail | drive | slack | done). "
        "Be concise. Output only the numbered list, no preamble."
    )
    return await chat([
        {"role": "system", "content": system},
        {"role": "user", "content": task_prompt},
    ])
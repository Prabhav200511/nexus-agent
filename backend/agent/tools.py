"""
Agent Tools — Tool execution ONLY.

Responsibilities:
  - Execute individual tools (web_search, browser, firecrawl, gmail, etc.)
  - Return structured ToolResult objects
  - Handle tool-level errors gracefully

NOT allowed here:
  - LangGraph graph definitions
  - Task planning or decomposition
  - DB/Redis persistence
  - HTTP handling
  - WebSocket communication
  - Deciding WHICH tool to run (that's the graph's job)

Each tool is a pure async function: input → output. Nothing else.
"""

import os
from dataclasses import dataclass


@dataclass
class ToolResult:
    success: bool
    output: str
    tool: str
    error: str | None = None


# ---------------------------------------------------------------------------
# Web Search
# ---------------------------------------------------------------------------

async def tool_web_search(query: str) -> ToolResult:
    """Search the web using a search API."""
    try:
        import httpx
        api_key = os.getenv("SEARCH_API_KEY", "")
        url = "https://api.tavily.com/search"

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json={
                "api_key": api_key,
                "query": query,
                "max_results": 5,
            })
            resp.raise_for_status()
            data = resp.json()

        results = data.get("results", [])
        formatted = "\n\n".join(
            f"[{r['title']}]({r['url']})\n{r.get('content', '')}" for r in results
        )
        return ToolResult(success=True, output=formatted or "No results found.", tool="web_search")

    except Exception as e:
        return ToolResult(success=False, output="", tool="web_search", error=str(e))


# ---------------------------------------------------------------------------
# Browser (browser-use + Playwright)
# ---------------------------------------------------------------------------

async def tool_browser(instruction: str) -> ToolResult:
    """
    Execute a natural language browser instruction via browser-use.
    browser-use translates the instruction into Playwright actions.
    """
    try:
        from browser_use import Agent as BrowserAgent
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            agent = BrowserAgent(
                task=instruction,
                browser=browser,
            )
            result = await agent.run()
            await browser.close()

        return ToolResult(success=True, output=str(result), tool="browser")

    except Exception as e:
        return ToolResult(success=False, output="", tool="browser", error=str(e))


# ---------------------------------------------------------------------------
# Firecrawl (web scraping → structured Markdown)
# ---------------------------------------------------------------------------

async def tool_firecrawl(url: str) -> ToolResult:
    """Scrape a URL and return structured Markdown via Firecrawl."""
    try:
        import httpx
        api_key = os.getenv("FIRECRAWL_API_KEY", "")

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.firecrawl.dev/v0/scrape",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"url": url, "pageOptions": {"onlyMainContent": True}},
            )
            resp.raise_for_status()
            data = resp.json()

        markdown = data.get("data", {}).get("markdown", "")
        return ToolResult(success=True, output=markdown or "No content extracted.", tool="firecrawl")

    except Exception as e:
        return ToolResult(success=False, output="", tool="firecrawl", error=str(e))


# ---------------------------------------------------------------------------
# Gmail (via MCP)
# ---------------------------------------------------------------------------

async def tool_gmail(to: str, subject: str, body: str) -> ToolResult:
    """Send an email via Gmail MCP connector."""
    try:
        import httpx
        mcp_url = os.getenv("MCP_GMAIL_URL", "http://localhost:4001")

        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(f"{mcp_url}/send", json={
                "to": to, "subject": subject, "body": body,
            })
            resp.raise_for_status()

        return ToolResult(success=True, output=f"Email sent to {to}", tool="gmail")

    except Exception as e:
        return ToolResult(success=False, output="", tool="gmail", error=str(e))


# ---------------------------------------------------------------------------
# Tool dispatcher — the ONLY place tool names map to functions
# ---------------------------------------------------------------------------

TOOL_REGISTRY: dict[str, callable] = {
    "web_search": tool_web_search,
    "browser": tool_browser,
    "firecrawl": tool_firecrawl,
    "gmail": tool_gmail,
}


async def dispatch_tool(tool_name: str, input_data: str) -> ToolResult:
    """
    Route a tool name to its implementation.
    Called exclusively by agent/graph.py — never by routers or services.
    """
    fn = TOOL_REGISTRY.get(tool_name)
    if not fn:
        return ToolResult(
            success=False, output="", tool=tool_name,
            error=f"Unknown tool: '{tool_name}'"
        )
    return await fn(input_data)
# NEXUS — Autonomous AI Agent Platform
## Shared Project State (Round-Robin AI Collaboration)

---

## 🤝 Collaboration Protocol

| Role | AI | Responsibility |
|------|----|----------------|
| **AI-1** | Claude (Anthropic) | Reviews GPT output, fills gaps, owns whatever GPT doesn't cover |
| **AI-2** | GPT | Builds assigned module, hands off via this file |
| **Coordinator** | Human | Triggers each round, commits files to GitHub |

### Round-Robin Rules
1. Each AI reads **PROJECT_STATE.md** + last commit diff before doing anything
2. Each AI updates this file at end of turn (done, issues found, next task)
3. Never overwrite another AI's completed ✅ file without logging it in Round Log
4. Flag conflicts or questions in **⚠️ Open Issues**
5. Mark: ✅ done · 🔄 in progress · ⬜ not started

---

## 📦 Project Overview

**What we're building:** An autonomous AI agent web platform where users submit natural language tasks and an AI agent plans + executes them using browser automation, APIs, and external tools — with human-in-the-loop approval for sensitive actions.

---

## 🏗️ Architecture

```
[Next.js Frontend] ←WebSocket→ [FastAPI Backend] → [LangGraph Agent Engine]
                                                          ↓
                                              [Tool Layer: browser-use, Firecrawl, MCP]
                                                          ↓
                                              [LLM: GPT-4o / Claude via LiteLLM]
                                                          ↓
                                              [Memory: PostgreSQL + Redis]
```

### Strict Layer Boundaries (DO NOT VIOLATE)

```
routers/tasks.py          → HTTP only. No LLM. No tools.
routers/ws.py             → WebSocket only. No LLM. No tools.
agent/executor.py         → ONLY bridge between HTTP and agent world.
agent/graph.py            → Orchestration only. Calls dispatch_tool(), never implements tools.
agent/planner.py          → LLM calls for planning only. No tool execution.
agent/tools.py            → Tool execution only. No routing. No DB. No HTTP.
services/memory.py        → DB + Redis only. No agent logic.
services/llm.py           → LiteLLM wrapper only. No tool calls.
models/task.py            → Data shapes only. No logic.
```

---

## 📁 Folder Structure

```
nexus/
├── frontend/                  # Next.js app (Phase 4)
│   ├── app/
│   │   ├── page.tsx
│   │   └── layout.tsx
│   ├── components/
│   │   ├── TaskInput.tsx
│   │   ├── ExecutionTrace.tsx
│   │   ├── ApprovalCard.tsx
│   │   ├── ToolPanel.tsx
│   │   └── TaskSidebar.tsx
│   └── lib/
│       └── websocket.ts
│
├── backend/
│   ├── main.py                ✅ Claude R2
│   ├── requirements.txt       ✅ Claude R2
│   ├── Dockerfile             ✅ GPT R1
│   ├── routers/
│   │   ├── tasks.py           ✅ Claude R2 (rewrote GPT's in-memory version)
│   │   └── ws.py              ✅ Claude R2 (rewrote GPT's echo stub)
│   ├── agent/
│   │   ├── graph.py           ✅ Claude R2
│   │   ├── tools.py           ✅ Claude R2
│   │   ├── planner.py         ✅ Claude R2
│   │   └── executor.py        ✅ Claude R2
│   ├── models/
│   │   └── task.py            ✅ Claude R2
│   └── services/
│       ├── memory.py          ✅ Claude R2
│       └── llm.py             ✅ Claude R2
│
├── docker-compose.yml         ✅ Claude R2 (upgraded from GPT R1)
├── .env.example               ✅ Claude R2
├── PROJECT_STATE.md           ✅
└── README.md                  ⬜
```

---

## ✅ Tech Stack (Locked)

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, Tailwind CSS, DaisyUI |
| Backend | Python 3.11, FastAPI, WebSockets |
| Agent Engine | LangGraph 0.2.x, LiteLLM |
| LLM | GPT-4o (primary), Claude claude-opus-4-6 (fallback) |
| Browser | browser-use + Playwright |
| Web Scraping | Firecrawl |
| Search | Tavily API |
| Tools | MCP (Gmail, Drive, Slack, GitHub) |
| Memory | PostgreSQL 15 + Redis 7 |
| Observability | LangSmith |
| Deployment | Docker, Vercel (FE), Railway (BE), Supabase, Upstash |

---

## 📋 Build Checklist

### Phase 1 — Foundation
- ✅ Project scaffolding (folder structure, configs)
- ✅ FastAPI app skeleton (main.py, CORS, lifespan, routers)
- ✅ Task model (Task, Step, TaskStatus, TaskCreate, TaskApproval)
- ✅ Tasks router (POST /tasks, GET /tasks, GET /tasks/{id}, POST /tasks/{id}/approve)
- ✅ WebSocket router (connection manager, task_id scoped, broadcast support)
- ✅ Docker Compose (postgres + healthcheck, redis + healthcheck, backend)
- ✅ requirements.txt
- ✅ .env.example
- ⬜ Next.js app skeleton (layout, pages)
- ⬜ Basic WebSocket connection FE ↔ BE (needs frontend)

### Phase 2 — Agent Core
- ✅ LangGraph agent graph (plan → check_approval → execute → summarize)
- ✅ Task planning node (via planner.py + llm.py)
- ✅ Human-in-the-loop checkpoint (LangGraph interrupt on sensitive tools)
- ✅ Agent executor (run_agent_task, resume_agent_task, WS broadcast)
- ✅ Tool dispatcher (dispatch_tool registry pattern)
- ✅ Tool: Web search (Tavily)
- ✅ Tool: browser-use + Playwright
- ✅ Tool: Firecrawl extraction
- ✅ Tool: Gmail (MCP stub)
- ✅ Redis short-term memory (cache_set/get/delete)
- ✅ Postgres task persistence (save, get, list, update)

### Phase 3 — Tools & Integrations
- ⬜ MCP Gmail connector (full integration test)
- ⬜ MCP Google Drive connector
- ⬜ MCP Slack connector
- ⬜ MCP GitHub connector

### Phase 4 — Frontend
- ⬜ Next.js project init (app router, Tailwind, DaisyUI)
- ⬜ Task input + submit (POST /tasks)
- ⬜ WebSocket hook (lib/websocket.ts)
- ⬜ Real-time execution trace (stream step updates)
- ⬜ Approval card UI (pause + approve/reject)
- ⬜ Task history sidebar
- ⬜ Tool status panel
- ⬜ Browser preview panel

### Phase 5 — Polish & Deploy
- ⬜ LangSmith observability wiring
- ⬜ Error handling + retries
- ⬜ Docker production build
- ⬜ Deploy frontend → Vercel
- ⬜ Deploy backend → Railway
- ⬜ Supabase + Upstash wiring

---

## 🔄 Round Log

### Round 0 — Claude (Setup)
**Date:** 2026-03-09
**Done:** PROJECT_STATE.md, protocol, folder structure, tech stack, UI mockup reference

---

### Round 1 — GPT
**Date:** 2026-03-11
**Done:**
- FastAPI skeleton (main.py)
- Task router stub (in-memory TASK_STORE)
- WebSocket echo stub
- Dockerfile
- docker-compose.yml (postgres, redis, backend)

**Issues found by Claude in review:**
- `TASK_STORE = {}` — in-memory only, lost on restart ❌
- WebSocket was a plain echo server, no task_id routing ❌
- No lifespan handler, DB/Redis never initialized ❌
- `allow_origins=["*"]` — too open ❌
- `requirements.txt` missing (Dockerfile referenced it) ❌
- Entire `agent/` folder empty ❌

---

### Round 2 — Claude
**Date:** 2026-03-11
**Done:**
- Rewrote `main.py` — lifespan handler, env-controlled CORS
- Rewrote `routers/tasks.py` — Postgres-backed, all endpoints including HITL approve
- Rewrote `routers/ws.py` — ConnectionManager, task_id scoped, broadcast()
- Added `models/task.py` — Task, Step, TaskStatus, TaskCreate, TaskApproval
- Added `services/memory.py` — asyncpg Postgres + Redis, full CRUD
- Added `services/llm.py` — LiteLLM wrapper, primary + fallback model
- Added `agent/planner.py` — LLM task decomposition, tool keyword detection
- Added `agent/tools.py` — isolated tool implementations + dispatch_tool registry
- Added `agent/graph.py` — LangGraph state machine, HITL interrupt, clean routing
- Added `agent/executor.py` — single HTTP↔agent bridge, WS broadcasting
- Added `requirements.txt` — all pinned dependencies
- Upgraded `docker-compose.yml` — healthchecks, env var substitution
- Added `.env.example` — all required variables documented

**Enforced architecture rule:** Agent/tool mixing fully prevented via strict import chain.

**Handing off to:** GPT

---

## 📋 Next Task for GPT — Phase 4 Frontend

Build the Next.js frontend. Files needed:

1. `frontend/package.json` — Next.js 14, Tailwind, DaisyUI, dependencies
2. `frontend/app/layout.tsx` — root layout with Tailwind
3. `frontend/app/page.tsx` — main dashboard page (imports components)
4. `frontend/lib/websocket.ts` — custom hook `useTaskSocket(taskId)` that connects to `ws://localhost:8000/ws/{taskId}` and streams events
5. `frontend/components/TaskInput.tsx` — text area + submit button, calls `POST /tasks`
6. `frontend/components/ExecutionTrace.tsx` — renders live step list from WebSocket stream
7. `frontend/components/ApprovalCard.tsx` — shown when event=`awaiting_approval`, calls `POST /tasks/{id}/approve`
8. `frontend/components/TaskSidebar.tsx` — fetches `GET /tasks`, shows history list
9. `frontend/components/ToolPanel.tsx` — displays tool name + status for each step

**WebSocket events to handle** (from backend):
- `connected` — initial ack
- `task_started` — show task prompt
- `step_update` — update step list with status + tool used
- `awaiting_approval` — show ApprovalCard
- `task_resumed` — hide ApprovalCard, continue trace
- `task_done` — show final result
- `task_failed` — show error state

**Style:** Use the visual design from `agent-platform.html` (dark theme, monospace accents) as reference.

Then update PROJECT_STATE.md marking completed items ✅ and what Claude should do next.

---

## ⚠️ Open Issues / Decisions Needed

| # | Issue | Status |
|---|-------|--------|
| 1 | Auth strategy — do we need user login? | ❓ Undecided |
| 2 | LangGraph v0.2 confirmed | ✅ Resolved |
| 3 | MCP server — self-hosted or cloud? | ❓ Undecided |
| 4 | Rate limiting / cost controls on LLM calls | ❓ Undecided |
| 5 | MemorySaver → RedisCheckpointer for production LangGraph state | ⬜ Needed before deploy |

---

## 📌 Conventions (Both AIs Must Follow)

- **Python:** snake_case, type hints everywhere, async/await throughout
- **TypeScript:** strict mode, named exports, no `any`
- **Git commits:** `[Claude] feat:` or `[GPT] feat:` prefix always
- **Env vars:** all secrets via `.env`, never hardcoded
- **API responses:** always `{ success: bool, data: any, error: str | null }`
- **Agent/Tool separation:** routers NEVER import from agent/. Only executor.py bridges them.
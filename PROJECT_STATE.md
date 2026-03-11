# NEXUS — Autonomous AI Agent Platform
## Shared Project State (Round-Robin AI Collaboration)

---

## 🤝 Collaboration Protocol

| Role | AI | Responsibility |
|------|----|----------------|
| **AI-1** | Claude (Anthropic) | Reviews GPT output, fills gaps, owns whatever GPT doesn't cover |
| **AI-2** | GPT | Builds assigned module, hands off via this file |
| **Coordinator** | Human | Pastes output between AIs, triggers each round |

### Round-Robin Rules
1. Each AI reads the **Current State** + **Last Handoff** before doing anything
2. Each AI updates this file at the end of its turn (what was done, what's next)
3. Never overwrite another AI's completed work — only extend or review it
4. Flag conflicts or questions in the **⚠️ Open Issues** section
5. Mark completed items with ✅, in-progress with 🔄, not started with ⬜

---

## 📦 Project Overview

**What we're building:** An autonomous AI agent web platform where users submit natural language tasks and an AI agent plans + executes them using browser automation, APIs, and external tools — with human-in-the-loop approval for sensitive actions.

**Example flow:**
> "Find cheapest flight MUM→TYO next month and email me options"
> Agent plans → searches web → opens browser → extracts prices → compares → asks approval → sends email

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

---

## 📁 Folder Structure (Agreed)

```
nexus/
├── frontend/                  # Next.js app
│   ├── app/
│   │   ├── page.tsx           # Main dashboard
│   │   ├── layout.tsx
│   │   └── api/               # Next.js API routes (if any)
│   ├── components/
│   │   ├── TaskInput.tsx
│   │   ├── ExecutionTrace.tsx
│   │   ├── ApprovalCard.tsx
│   │   ├── ToolPanel.tsx
│   │   └── TaskSidebar.tsx
│   └── lib/
│       └── websocket.ts       # WS client hook
│
├── backend/                   # FastAPI
│   ├── main.py                # Entry point
│   ├── routers/
│   │   ├── tasks.py           # Task CRUD endpoints
│   │   └── ws.py              # WebSocket handler
│   ├── agent/
│   │   ├── graph.py           # LangGraph workflow
│   │   ├── tools.py           # Tool definitions
│   │   ├── planner.py         # Task decomposition
│   │   └── executor.py        # Step execution loop
│   ├── models/
│   │   └── task.py            # DB models
│   └── services/
│       ├── memory.py          # Redis + Postgres helpers
│       └── llm.py             # LiteLLM wrapper
│
├── docker-compose.yml
├── PROJECT_STATE.md           # ← THIS FILE (always up to date)
└── README.md
```

---

## ✅ Tech Stack (Locked)

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, Tailwind CSS, DaisyUI |
| Backend | Python, FastAPI, WebSockets |
| Agent Engine | LangGraph, LiteLLM |
| LLM | GPT-4o (primary), Claude (fallback) |
| Browser | browser-use + Playwright |
| Web Scraping | Firecrawl |
| Tools | MCP (Gmail, Drive, Slack, GitHub) |
| Memory | PostgreSQL + Redis |
| Observability | LangSmith |
| Deployment | Docker, Vercel (FE), Railway (BE), Supabase, Upstash |

---

## 📋 Build Checklist

### Phase 1 — Foundation
- ⬜ Project scaffolding (folder structure, configs)
- ⬜ FastAPI app skeleton (main.py, routers)
- ⬜ Next.js app skeleton (layout, pages)
- ⬜ Docker Compose (postgres, redis, backend, frontend)
- ⬜ Basic WebSocket connection FE ↔ BE

### Phase 2 — Agent Core
- ⬜ LangGraph agent graph definition
- ⬜ Task planning node (LiteLLM call)
- ⬜ Tool node: Web search
- ⬜ Tool node: browser-use + Playwright
- ⬜ Tool node: Firecrawl extraction
- ⬜ Human-in-the-loop checkpoint (LangGraph interrupt)
- ⬜ Redis short-term memory
- ⬜ Postgres task persistence

### Phase 3 — Tools & Integrations
- ⬜ MCP Gmail connector
- ⬜ MCP Google Drive connector
- ⬜ MCP Slack connector
- ⬜ MCP GitHub connector

### Phase 4 — Frontend
- ⬜ Task input + submit
- ⬜ Real-time execution trace (WebSocket stream)
- ⬜ Approval card UI (pause + resume)
- ⬜ Task history sidebar
- ⬜ Tool status panel
- ⬜ Browser preview panel

### Phase 5 — Polish & Deploy
- ⬜ LangSmith observability integration
- ⬜ Error handling + retries
- ⬜ Docker production build
- ⬜ Deploy frontend → Vercel
- ⬜ Deploy backend → Railway
- ⬜ Supabase + Upstash wiring

---

## 🔄 Round Log

### Round 0 — Claude (Setup)
**Date:** 2026-03-09
**Done:**
- Created PROJECT_STATE.md (this file)
- Defined collaboration protocol
- Locked folder structure, tech stack, build checklist
- UI mockup already built (agent-platform.html) as visual reference

**Handing off to:** GPT
**Suggested next task for GPT:** 
> Build Phase 1 — Project scaffolding:
> - `backend/main.py` (FastAPI skeleton with CORS, health check, router stubs)
> - `backend/routers/tasks.py` (POST /tasks, GET /tasks/{id})
> - `backend/routers/ws.py` (WebSocket endpoint stub)
> - `docker-compose.yml` (postgres, redis, backend services)
> 
> Then update PROJECT_STATE.md: mark completed items ✅, add what Claude should do next.

---

## ⚠️ Open Issues / Decisions Needed

| # | Issue | Status |
|---|-------|--------|
| 1 | Auth strategy — do we need user login? | ❓ Undecided |
| 2 | Which LangGraph version? (v0.1 vs v0.2 API) | ❓ Undecided |
| 3 | MCP server — self-hosted or cloud? | ❓ Undecided |
| 4 | Rate limiting / cost controls on LLM calls | ❓ Undecided |

---

## 📌 Conventions (Both AIs Must Follow)

- **Python:** snake_case, type hints everywhere, async/await throughout
- **TypeScript:** strict mode, named exports, no `any`
- **Git commits:** `feat:`, `fix:`, `refactor:` prefixes
- **Env vars:** all secrets via `.env`, never hardcoded
- **API responses:** always `{ success: bool, data: any, error: str | null }`
# Redis Iris Workshop

## What This Is

A hands-on developer workshop where learners pick an industry domain and build an AI support agent step-by-step using Redis Iris components. Learners edit 5 exercise files in `exercises/<domain>/` — everything else is pre-built.

**Domains:** digital-native (Redis Eats), healthcare (RedHealthConnect), retail (ElectroHub), finance (ShiftIQ), banking (Radish Bank). Selected via `DEMO_DOMAIN` env var (default: digital-native).

## Running

```bash
make install    # uv sync + npm install
make seed-data  # load policies into Redis
make dev        # backend :8040, frontend :3040
```

Set `USE_SOLUTIONS=1` to run with all exercises pre-filled.

## Architecture

- **Exercises** (`exercises/<domain>/`): The 5 files learners implement per domain. Each subclasses a base from `backend/app/bases/` and overrides 2-3 hook methods.
- **Base Classes** (`backend/app/bases/`): Pre-built boilerplate — HTTP clients, error handling, SSE streaming. Exercise files inherit from these.
- **Service Re-exports** (`backend/app/services/`): Use `importlib.import_module(f"exercises.{DEMO_DOMAIN}...")` to dynamically load the active domain's exercises. Supports `USE_SOLUTIONS` env var to switch to reference implementations.
- **Solutions** (`exercises/<domain>/solutions/`): Complete exercise implementations per domain.
- **Backend** (`backend/app/`): FastAPI + SSE streaming (`main.py`), LangGraph ReAct agent (`langgraph_agent.py`).
- **Frontend** (`frontend/`): React + Vite. Polls `/api/status` to conditionally show features. Dynamic backgrounds/logos per domain via CSS custom properties.
- **Domains** (`domains/<domain>/`): Each domain has schema, system prompt, data generator, branding, and seed data config.

## Key Patterns

- `/api/status` returns which services are configured — drives progressive UI reveal
- Each base class's `is_configured()` checks both credentials AND exercise implementation
- The hook pattern: base class provides boilerplate, exercise overrides methods that return `None` by default
- Two data loading phases: `make seed-data` (redis-py direct) and `make setup-surface && make load-data` (Context Surfaces SDK)
- Pre-generated JSONL data in `output/<domain>/` includes embeddings
- Frontend backgrounds in `frontend/public/backgrounds/<domain>/left.svg, right.svg`

## Module Order

0. Setup (Redis Cloud + env)
1. Vector Search (`exercises/<domain>/vector_search.py`) — VectorQuery with redisvl
2. Semantic Router (`exercises/<domain>/semantic_router.py`) — Route definitions + classification
3. Context Retriever (`exercises/<domain>/context_retriever.py`) — cloud setup + guided exploration (no code exercise)
4. LangCache (`exercises/<domain>/langcache.py`) — cache search/store request bodies
5. Agent Memory (`exercises/<domain>/agent_memory.py`) — session event + memory search payloads

## Conventions

- Python 3.11+, managed with uv
- Ruff for linting (line-length 100)
- Import chain: `main.py` → `services/` (re-exports) → `exercises/` → `bases/`
- Settings via pydantic-settings from `.env`

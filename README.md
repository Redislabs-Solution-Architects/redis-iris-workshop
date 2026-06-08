# Redis Iris Workshop

Build a fully functional AI-powered food delivery support agent — step by step — using **Redis Iris**, the unified context engine for AI applications.

## Quick Start

```bash
git clone <repo-url> && cd redis-iris-workshop
make install
cp .env.example .env   # fill in Redis + OpenAI credentials
make seed-data
make dev
```

Open [localhost:3040](http://localhost:3040) for the app, and follow the [workshop guide](https://redis-iris-workshop.vercel.app).

## What You'll Build

**Redis Eats** — a food delivery support agent with 5 Redis Iris components:

| # | Module | What You'll Add | Exercise File |
|---|--------|----------------|---------------|
| 0 | Setup | Redis Cloud database | — |
| 1 | Vector Search | RAG over policy documents | `exercises/vector_search.py` |
| 2 | Semantic Router | Off-topic query guardrails | `exercises/semantic_router.py` |
| 3 | LangCache | Semantic caching | `exercises/langcache.py` |
| 4 | Context Retriever | Real-time data via MCP tools | `exercises/context_retriever.py` |
| 5 | Agent Memory | Session + long-term memory | `exercises/agent_memory.py` |

## How It Works

You only edit **5 exercise files** in `exercises/` — everything else is pre-built. Each exercise is ~10-25 lines of Redis-specific code. The boilerplate lives in `backend/app/bases/`.

After each module, restart the app and watch the new capability appear in the UI.

## Workshop Guide

The full workshop guide is at **[redis-iris-workshop.vercel.app](https://redis-iris-workshop.vercel.app)** — open it in a separate tab as you work through the exercises.

## Project Structure

```
exercises/                  ← You edit these (5 files)
exercises/solutions/        ← Reference implementations
backend/app/bases/          ← Pre-built boilerplate
backend/app/services/       ← Re-export layer (don't edit)
backend/app/                ← Frozen infrastructure
frontend/                   ← React + Vite UI
scripts/                    ← Data seeding
output/<domain>/             ← Pre-generated data
```

## Make Targets

```
make install              Install all dependencies
make dev                  Run backend + frontend
make seed-data            Load policies into Redis (Module 0)
make seed-langcache       Seed a cache entry (Module 3)
make setup-surface        Create Context Surface (Module 4)
make load-data            Load entity data (Module 4)
make seed-memories        Seed long-term memories (Module 5)
make status               Check which modules are active
make reset                Flush Redis + re-seed
```

## Prerequisites

- Python 3.11+ and [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Node.js 18+ and npm
- [Redis Cloud](https://redis.io/try-free/) account (free tier)
- OpenAI API key (provided by instructor)

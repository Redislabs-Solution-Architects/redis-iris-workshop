# Redis Iris Workshop

Build a smarter, faster AI agent with [Redis Iris](https://redis.io/iris/)  hands on, step by step.

> **Workshop Guide** → [redis-iris-workshop.vercel.app](https://redis-iris-workshop.vercel.app)

## What is this?

A hands on workshop where you pick an industry vertical and build an AI support agent powered by Redis Iris. You edit 5 exercise files. Everything else is pre-built.

**Pick a vertical:**

| Vertical | Agent | Domain Key |
|----------|-------|------------|
| Digital Native | Food delivery support | `digital-native` |
| Healthcare | Patient portal assistant | `healthcare` |
| Retail | Electronics shopping concierge | `retail` |
| Finance | Stock research analyst | `finance` |
| Banking | Customer care agent | `banking` |

## Quick Start

```bash
git clone https://github.com/Redislabs-Solution-Architects/redis-iris-workshop.git
cd redis-iris-workshop
make install
cp .env.example .env   # fill in Redis + OpenAI credentials
make seed-data
make dev
```

Open [localhost:3040](http://localhost:3040) and follow the [workshop guide](https://redis-iris-workshop.vercel.app).

## What You Build

Each module adds one Redis Iris capability to your agent:

| # | Module | What You Add | Exercise File |
|---|--------|-------------|---------------|
| 0 | Setup | Redis Cloud database + environment | — |
| 1 | Vector Search | Search policy documents by meaning | `exercises/<domain>/vector_search.py` |
| 2 | Semantic Router | Block off topic queries before the LLM | `exercises/<domain>/semantic_router.py` |
| 3 | Context Retriever | Query live business data | `exercises/<domain>/context_retriever.py` |
| 4 | LangCache | Cache responses so repeats return instantly | `exercises/<domain>/langcache.py` |
| 5 | Agent Memory | Remember users across conversations | `exercises/<domain>/agent_memory.py` |

## Project Structure

```
exercises/<domain>/             ← You edit these (5 files per domain)
exercises/<domain>/solutions/   ← Reference implementations
backend/app/bases/              ← Pre-built boilerplate
backend/app/services/           ← Dynamic import layer (don't edit)
backend/app/                    ← FastAPI + LangGraph agent
frontend/                       ← React + Vite
domains/<domain>/               ← Schema, prompts, branding per vertical
scripts/                        ← Data seeding
```

## Make Targets

| Command | Description |
|---------|-------------|
| `make install` | Install all dependencies |
| `make dev` | Run backend + frontend |
| `make seed-data` | Module 0 — Load policies into Redis |
| `make setup-surface` | Module 3 — Create Context Surface + agent key |
| `make load-data` | Module 3 — Load entity data |
| `make seed-langcache` | Module 4 — Seed a LangCache entry |
| `make seed-memories` | Module 5 — Seed long term memories |
| `make status` | Check which modules are active |
| `make reset` | Flush Redis + re-seed |

## Prerequisites

- Python 3.11+ and [uv](https://docs.astral.sh/uv/getting-started/installation/)
- Node.js 18+ and npm
- [Redis Cloud](https://redis.io/try-free/) account (free tier)
- OpenAI API key (provided by instructor)

## Solutions

Set `USE_SOLUTIONS=1` in your `.env` to run with all exercises pre-filled.

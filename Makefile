BACKEND_HOST ?= 127.0.0.1
BACKEND_PORT ?= 8040
FRONTEND_PORT ?= 3040
DOMAIN ?= $(or $(shell grep -s '^DEMO_DOMAIN=' .env | cut -d= -f2),digital-native)

.PHONY: help install backend-install frontend-install dev backend frontend \
	seed-data setup-surface load-data seed-langcache seed-memories \
	generate-data generate-models status reset flush-redis

help:
	@echo ""
	@echo "  Redis Iris Workshop"
	@echo "  ─────────────────────────────────────────"
	@echo ""
	@echo "  Setup:"
	@echo "    make install          Install backend + frontend dependencies"
	@echo "    make dev              Run backend + frontend"
	@echo ""
	@echo "  Data (run in module order):"
	@echo "    make seed-data        Module 0 — Load policies into Redis for Simple RAG"
	@echo "    make setup-surface    Module 3 — Create Context Surface + agent key"
	@echo "    make load-data        Module 3 — Load all entities via Context Surfaces"
	@echo "    make seed-langcache   Module 4 — Seed one LangCache entry"
	@echo "    make seed-memories    Module 5 — Seed long-term memories"
	@echo ""
	@echo "  Utilities:"
	@echo "    make status           Check which modules are active"
	@echo "    make reset            Flush Redis + re-seed everything"
	@echo ""

backend-install:
	@uv sync

frontend-install:
	@cd frontend && npm install

install: backend-install frontend-install

backend:
	@uv run uvicorn backend.app.main:app --reload --host $(BACKEND_HOST) --port $(BACKEND_PORT)

frontend:
	@cd frontend && npm run dev -- --host 0.0.0.0 --port $(FRONTEND_PORT)

dev:
	@echo ""
	@echo "  ══════════════════════════════════════════════════"
	@echo "   Redis Iris Workshop"
	@echo ""
	@echo "   Workshop Guide:  https://redis-iris-workshop.vercel.app"
	@echo "   App:             http://localhost:$(FRONTEND_PORT)"
	@echo "   API:             http://localhost:$(BACKEND_PORT)"
	@echo "  ══════════════════════════════════════════════════"
	@echo ""
	@trap 'kill 0' EXIT; $(MAKE) backend & $(MAKE) frontend & wait

# ── Module 0: Seed policy data for Simple RAG ──
seed-data:
	@uv run python scripts/seed_data.py --domain $(DOMAIN)

# ── Module 3: Context Retriever ──
setup-surface:
	@uv run python scripts/setup_surface.py --domain $(DOMAIN)

load-data:
	@uv run python scripts/load_data.py --domain $(DOMAIN)

# ── Module 4: Seed LangCache ──
seed-langcache:
	@uv run python -m scripts.seed_langcache --domain $(DOMAIN)

# ── Module 5: Agent Memory ──
seed-memories:
	@uv run python -m scripts.seed_memories --domain $(DOMAIN)

# ── Utilities ──
status:
	@curl -s http://$(BACKEND_HOST):$(BACKEND_PORT)/api/status | python3 -m json.tool

generate-models:
	@uv run python scripts/generate_models.py --domain $(DOMAIN)

generate-data:
	@uv run python scripts/generate_data.py --domain $(DOMAIN)

flush-redis:
	@uv run python scripts/flush_redis.py

reset: flush-redis
	@echo "Re-seeding policy data..."
	@$(MAKE) seed-data
	@echo ""
	@echo "Reset complete. Run 'make dev' to start."

"""Base class for Module 2: Semantic Router (Guardrails).

Subclasses only need to override ``define_routes`` to complete the exercise.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from openai import AsyncOpenAI
from redisvl.extensions.router import Route, SemanticRouter
from redisvl.utils.vectorize import OpenAITextVectorizer

from backend.app.redis_connection import build_redis_url
from backend.app.settings import Settings

log = logging.getLogger("workshop.guardrail")


class GuardrailBase:
    """Absorbs all routing / embedding boilerplate for the Semantic Router."""

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def __init__(self, settings: Settings) -> None:
        self._openai_api_key: str = settings.openai_api_key
        self._embedding_model: str = settings.openai_embedding_model
        self._redis_url: str = build_redis_url(settings)
        self._enabled: bool = settings.guardrail_enabled
        self._openai = AsyncOpenAI(api_key=settings.openai_api_key)
        self._router: SemanticRouter | None = None
        self._lock = asyncio.Lock()

    def is_configured(self) -> bool:
        """Return True when credentials are present AND routes are defined."""
        if not (self._enabled and self._openai_api_key and self._redis_url):
            return False
        routes = self.define_routes()
        return bool(routes)

    # ------------------------------------------------------------------
    # Internals (pre-built)
    # ------------------------------------------------------------------

    async def _ensure_router(self) -> SemanticRouter | None:
        if self._router is not None:
            return self._router
        async with self._lock:
            if self._router is not None:
                return self._router
            vectorizer = OpenAITextVectorizer(
                model=self._embedding_model,
                api_config={"api_key": self._openai_api_key},
            )
            routes = self.define_routes()
            if not routes:
                return None

            def _build() -> SemanticRouter:
                return SemanticRouter(
                    name="workshop-guardrails",
                    vectorizer=vectorizer,
                    routes=routes,
                    redis_url=self._redis_url,
                    overwrite=False,
                )

            self._router = await asyncio.to_thread(_build)
            return self._router

    # ------------------------------------------------------------------
    # Hook method — override this in the exercise
    # ------------------------------------------------------------------

    def define_routes(self) -> list[Route] | None:
        """Return a list of Route objects for semantic classification."""
        return None

    # ------------------------------------------------------------------
    # Classification (pre-built)
    # ------------------------------------------------------------------

    def _classify_result(self, match_name: str, match_distance: float) -> dict:
        """Classify a route match: allow list passes, deny list blocks."""
        return {
            "allowed": match_name == "allow_list",
            "route": match_name,
            "distance": match_distance,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def embed(self, text: str) -> list[float]:
        """Generate an embedding vector for the given text."""
        resp = await self._openai.embeddings.create(
            input=[text], model=self._embedding_model
        )
        return resp.data[0].embedding

    async def check(self, vector: list[float]) -> dict:
        """Route a vector through the semantic router and classify the result."""
        try:
            router = await self._ensure_router()
            if router is None:
                return {"allowed": True, "route": None, "distance": None}
            match = await asyncio.to_thread(router, None, vector)
            return self._classify_result(match.name, match.distance)
        except Exception:
            return {"allowed": True, "route": None, "distance": None}

    async def close(self) -> None:
        """Clean up resources."""
        pass

"""Base class for Module 1: Simple RAG — Vector Search.

Absorbs all boilerplate: OpenAI client, index discovery, embedding,
search execution with retry, and SSE streaming. The exercise overrides
only create_vector_query().
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncIterator

from openai import AsyncOpenAI
from redisvl.index import SearchIndex
from redisvl.query import VectorQuery

from backend.app.core.domain_loader import get_active_domain
from backend.app.redis_connection import (
    RESILIENT_CONNECTION_KWARGS,
    build_redis_url,
    create_redis_client,
)
from backend.app.settings import Settings

log = logging.getLogger("workshop.rag")


def _discover_index(settings: Settings, *, name_contains: str) -> str:
    client = create_redis_client(settings)
    indexes = client.execute_command("FT._LIST")
    for idx in indexes:
        name = idx if isinstance(idx, str) else idx.decode()
        if name_contains.lower() in name.lower():
            return name
    raise RuntimeError(
        f"No matching search index found for '{name_contains}'. "
        "Did you run `make seed-data`?"
    )


def _sse(event_type: str, **fields: Any) -> str:
    return f"data: {json.dumps({'type': event_type, **fields})}\n\n"


class SimpleRAGBase:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.domain = get_active_domain(settings)
        self.openai = AsyncOpenAI(api_key=settings.openai_api_key)
        self._index: SearchIndex | None = None
        self._index_name: str | None = None

    # ── Hook method (override in exercise) ────────────────────

    def create_vector_query(
        self, embedding: list[float], rag_config: Any
    ) -> VectorQuery | None:
        return None

    # ── Pre-built context formatting ───────────────────────────

    def _build_rag_context(
        self, results: list[dict[str, Any]], rag_config: Any
    ) -> str:
        if not results:
            return ""
        return "\n\n".join(
            f"**{r.get('title', 'Document')}** ({r.get('category', '')}):\n"
            f"{r.get('content', '')}"
            for r in results
        )

    # ── Pre-built infrastructure ────────────────────────────────

    def is_configured(self) -> bool:
        if not (self.settings.openai_api_key and self.settings.redis_host):
            return False
        rag = self.domain.manifest.rag
        try:
            probe = self.create_vector_query([], rag)
        except Exception:
            return False
        return probe is not None

    def _get_index(self) -> SearchIndex:
        if self._index is None:
            rag = self.domain.manifest.rag
            self._index_name = _discover_index(
                self.settings, name_contains=rag.index_name_contains
            )
            self._index = SearchIndex.from_existing(
                self._index_name,
                redis_url=build_redis_url(self.settings),
                connection_kwargs=RESILIENT_CONNECTION_KWARGS,
            )
        return self._index

    async def _embed(self, text: str) -> list[float]:
        resp = await self.openai.embeddings.create(
            input=[text],
            model=self.settings.openai_embedding_model,
        )
        return resp.data[0].embedding

    def _search_policies(
        self, embedding: list[float], rag_config: Any
    ) -> list[dict[str, Any]]:
        query = self.create_vector_query(embedding, rag_config)
        if query is None:
            return []
        try:
            return self._get_index().query(query)
        except (ConnectionError, TimeoutError, OSError):
            self._index = None
            return self._get_index().query(query)

    async def stream_answer(
        self, question: str, timer: Any
    ) -> AsyncIterator[str]:
        rag = self.domain.manifest.rag
        yield _sse("status", text="Embedding query…", ts=timer.elapsed_ms())
        embedding = await self._embed(question)

        query = self.create_vector_query(embedding, rag)
        num_results = getattr(query, "_num_results", rag.num_results) if query else rag.num_results

        yield _sse(
            "status", text=rag.status_text, ts=timer.elapsed_ms()
        )
        yield _sse(
            "tool-call",
            toolName=rag.tool_name,
            toolKind="internal_function",
            payload={"query": question, "num_results": num_results},
            ts=timer.elapsed_ms(),
        )

        timer.lap_ms()
        if query is None:
            results = []
        else:
            try:
                results = self._get_index().query(query)
            except (ConnectionError, TimeoutError, OSError):
                self._index = None
                results = self._get_index().query(query)
        search_duration = timer.lap_ms()

        search_payload = [
            {k: v for k, v in r.items() if k != rag.vector_field}
            for r in results
        ]
        yield _sse(
            "tool-result",
            toolName=rag.tool_name,
            toolKind="internal_function",
            payload={"results": search_payload},
            durationMs=search_duration,
            ts=timer.elapsed_ms(),
        )

        yield _sse(
            "status",
            text=f"Found {len(results)} matching documents. {rag.generating_text}",
            ts=timer.elapsed_ms(),
        )

        context_text = self._build_rag_context(results, rag)

        system_prompt = (
            f"{rag.answer_system_prompt}\n\n"
            f"--- DOMAIN DOCUMENTS ---\n{context_text}\n--- END ---"
        )
        try:
            stream = await self.openai.chat.completions.create(
                model=self.settings.openai_chat_model,
                temperature=0.2,
                stream=True,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                if delta:
                    yield _sse("text-delta", delta=delta)
        except Exception:
            yield _sse(
                "text-delta",
                delta="Sorry, I wasn't able to generate a response. Please try again.",
            )

"""Base class for Module 5: Agent Memory (Session + Long-Term).

Subclasses only need to override ``long_term_search_payload`` to complete the exercise.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Literal

import httpx

from backend.app.settings import Settings

# ------------------------------------------------------------------
# Module-level utilities (importable by other modules)
# ------------------------------------------------------------------

MessageRole = Literal["USER", "ASSISTANT", "SYSTEM"]


def _sanitize_id(value: str | None, *, fallback: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", (value or "").strip()).strip("-")
    return cleaned or fallback


def sanitize_owner_id(value: str | None) -> str:
    return _sanitize_id(value, fallback="unknown-owner")


def sanitize_actor_id(value: str | None) -> str:
    return _sanitize_id(value, fallback="reddash-agent")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def extract_memory_items(payload: Any) -> list:
    if not isinstance(payload, dict):
        return []
    items = payload.get("items")
    if isinstance(items, list):
        return items
    memories = payload.get("memories")
    if isinstance(memories, list):
        return memories
    return []


# ------------------------------------------------------------------
# Base class
# ------------------------------------------------------------------


class MemoryBase:
    """Absorbs all HTTP / lifecycle boilerplate for Agent Memory."""

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._async_client: httpx.AsyncClient | None = None

    def is_configured(self) -> bool:
        """Return True when credentials are present AND hooks are implemented."""
        if not (
            self.settings.memory_api_base_url
            and self.settings.memory_store_id
            and self.settings.memory_api_key
        ):
            return False
        # Probe the hook -- if it still returns None the exercise is incomplete.
        probe = self.long_term_search_payload(
            text="probe",
            owner_id="probe",
            session_id=None,
            limit=None,
        )
        return probe is not None

    # ------------------------------------------------------------------
    # Internals (pre-built)
    # ------------------------------------------------------------------

    def _get_async_client(self) -> httpx.AsyncClient:
        if self._async_client is None or self._async_client.is_closed:
            self._async_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0, connect=10.0),
            )
        return self._async_client

    def _headers(self) -> dict[str, str]:
        api_key = self.settings.memory_api_key
        if not api_key.lower().startswith(("bearer ", "basic ")):
            api_key = f"Bearer {api_key}"
        return {
            "Authorization": api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    def _url(self, path: str) -> str:
        base = self.settings.memory_api_base_url.rstrip("/")
        store_id = self.settings.memory_store_id
        return f"{base}/v1/stores/{store_id}{path}"

    def _search_filter(self, session_id: str | None = None) -> dict:
        owner_id = sanitize_owner_id(self.settings.memory_owner_id)
        namespace = self.settings.memory_namespace.strip() or "reddash-demo"
        filt: dict[str, Any] = {
            "ownerId": {"eq": owner_id},
            "namespace": {"eq": namespace},
        }
        if session_id:
            filt["sessionId"] = {"eq": session_id}
        return filt

    # ------------------------------------------------------------------
    # Convenience helpers exposed as methods for exercise use
    # ------------------------------------------------------------------

    @staticmethod
    def _sanitize_actor_id(value: str | None) -> str:
        """Sanitize an actor ID (delegates to the module-level function)."""
        return sanitize_actor_id(value)

    @staticmethod
    def _utc_now_iso() -> str:
        """Return the current UTC time as an ISO-8601 string."""
        return utc_now_iso()

    # ------------------------------------------------------------------
    # Hook methods -- override these in the exercise
    # ------------------------------------------------------------------

    def session_event_payload(
        self,
        *,
        actor_id: str,
        role: str,
        text: str,
        session_id: str | None,
        metadata: dict | None,
    ) -> dict | None:
        """Return the JSON body for a session memory event."""
        payload: dict[str, Any] = {
            "actorId": self._sanitize_actor_id(actor_id),
            "role": role,
            "content": [{"text": text}],
            "createdAt": self._utc_now_iso(),
            "metadata": metadata or {},
        }
        if session_id:
            payload["sessionId"] = session_id
        return payload

    def long_term_search_payload(
        self,
        *,
        text: str,
        owner_id: str,
        session_id: str | None,
        limit: int | None,
    ) -> dict | None:
        """Return the JSON body for a long-term memory search, or None if not implemented."""
        return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def add_session_event(
        self,
        *,
        owner_id: str,
        session_id: str | None,
        actor_id: str,
        role: str,
        text: str,
        metadata: dict | None = None,
    ) -> dict:
        """Post a session memory event."""
        payload = self.session_event_payload(
            actor_id=actor_id,
            role=role,
            text=text,
            session_id=session_id,
            metadata=metadata,
        )
        if payload is None:
            return {}

        client = self._get_async_client()
        response = await client.post(
            self._url("/session-memory/events"),
            headers=self._headers(),
            json=payload,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Memory API {response.status_code}: {response.text}")
        return response.json() if response.content else {}

    async def get_session(self, *, owner_id: str, session_id: str) -> dict:
        """Retrieve session memory (fully pre-built, no hook needed)."""
        client = self._get_async_client()
        response = await client.get(
            self._url(f"/session-memory/{session_id}"),
            headers=self._headers(),
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Memory API {response.status_code}: {response.text}")
        return response.json() if response.content else {}

    async def asearch_long_term_memory(
        self,
        *,
        text: str,
        owner_id: str,
        session_id: str | None = None,
        limit: int | None = None,
    ) -> list:
        """Search long-term memory for relevant entries."""
        payload = self.long_term_search_payload(
            text=text,
            owner_id=owner_id,
            session_id=session_id,
            limit=limit,
        )
        if payload is None:
            return []

        client = self._get_async_client()
        response = await client.post(
            self._url("/long-term-memory/search"),
            headers=self._headers(),
            json=payload,
        )
        if response.status_code >= 400:
            raise RuntimeError(f"Memory API {response.status_code}: {response.text}")
        body = response.json() if response.content else {}
        return extract_memory_items(body)

    async def close(self) -> None:
        """Shut down the underlying HTTP client."""
        if self._async_client and not self._async_client.is_closed:
            await self._async_client.aclose()
            self._async_client = None

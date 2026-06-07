"""Base class for Module 4: LangCache (Semantic Caching).

Subclasses only need to override ``search_request_body`` to complete the exercise.
"""

from __future__ import annotations

import logging

import httpx

from backend.app.settings import Settings

log = logging.getLogger("workshop.langcache")


class LangCacheBase:
    """Absorbs all HTTP / lifecycle boilerplate for LangCache."""

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def __init__(self, settings: Settings) -> None:
        self._host: str = (settings.langcache_host or "").rstrip("/")
        self._cache_id: str = settings.langcache_cache_id or ""
        self._api_key: str = settings.langcache_api_key or ""
        self._threshold: float = settings.langcache_threshold
        self._client: httpx.AsyncClient | None = None

    def has_credentials(self) -> bool:
        """Return True when LangCache credentials are present."""
        return bool(self._host and self._cache_id and self._api_key)

    def is_configured(self) -> bool:
        """Return True when credentials are present AND hooks are implemented."""
        if not self.has_credentials():
            return False
        return self.search_request_body("") is not None

    # ------------------------------------------------------------------
    # Internals (pre-built)
    # ------------------------------------------------------------------

    def _base_url(self) -> str:
        return f"{self._host}/v1/caches/{self._cache_id}"

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client

    # ------------------------------------------------------------------
    # Hook methods — override these in the exercise
    # ------------------------------------------------------------------

    def search_request_body(self, prompt: str) -> dict | None:
        """Return the JSON body for a cache search, or None if not implemented."""
        return None

    def store_request_body(
        self,
        prompt: str,
        response: str,
        attributes: dict | None = None,
    ) -> dict | None:
        """Return the JSON body for a cache store."""
        body: dict = {"prompt": prompt, "response": response}
        if attributes:
            body["attributes"] = attributes
        return body

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def search(self, prompt: str) -> dict | None:
        """Search the semantic cache for a matching entry."""
        if not self.is_configured():
            return None

        body = self.search_request_body(prompt)
        if body is None:
            return None

        client = await self._get_client()
        try:
            resp = await client.post(
                f"{self._base_url()}/entries/search",
                headers=self._headers(),
                json=body,
            )
            resp.raise_for_status()
            data = resp.json()
            entries = data.get("data", [])
            if entries:
                best = entries[0]
                return {
                    "hit": True,
                    "similarity": best.get("similarity", 0),
                    "response": best.get("response", ""),
                    "prompt": best.get("prompt", ""),
                }
            return None
        except Exception:
            return None

    async def store(
        self,
        prompt: str,
        response: str,
        attributes: dict | None = None,
    ) -> bool:
        """Store a prompt/response pair in the semantic cache."""
        if not self.has_credentials():
            return False

        body = self.store_request_body(prompt, response, attributes)
        if body is None:
            return False

        client = await self._get_client()
        try:
            url = f"{self._base_url()}/entries"
            resp = await client.post(url, headers=self._headers(), json=body)
            resp.raise_for_status()
            return True
        except httpx.HTTPStatusError as exc:
            log.warning("LangCache store failed: %s — body: %s", exc, exc.response.text)
            return False
        except Exception as exc:
            log.warning("LangCache store failed: %s", exc)
            return False

    async def close(self) -> None:
        """Shut down the underlying HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

"""Base class for Module 3: Context Retriever (MCP Tools).

Fully pre-built — no exercise overrides needed. The exercise for this
module is cloud setup + guided exploration, not code.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from backend.app.settings import Settings

try:
    from context_surfaces import UnifiedClient
except ImportError:
    UnifiedClient = None

log = logging.getLogger("workshop.mcp")


class ContextSurfaceBase:
    """Absorbs all MCP client / lifecycle boilerplate for Context Surfaces."""

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._tool_cache: list[dict] | None = None
        self._client: UnifiedClient | None = None

    def is_configured(self) -> bool:
        """Return True when the MCP agent key is set."""
        return UnifiedClient is not None and bool(self.settings.mcp_agent_key)

    # ------------------------------------------------------------------
    # Internals (pre-built)
    # ------------------------------------------------------------------

    async def _get_client(self) -> UnifiedClient:
        if self._client is None:
            self._client = UnifiedClient()
            await self._client.__aenter__()
        return self._client

    async def _reset_client(self) -> UnifiedClient:
        try:
            if self._client is not None:
                await self._client.__aexit__(None, None, None)
        except Exception:
            pass
        self._client = None
        return await self._get_client()

    async def close(self) -> None:
        """Shut down the underlying MCP client."""
        if self._client is not None:
            await self._client.__aexit__(None, None, None)
            self._client = None

    # ------------------------------------------------------------------
    # Response parsing (pre-built)
    # ------------------------------------------------------------------

    def _parse_tool_response(self, raw_result: Any) -> dict:
        """Parse a raw MCP tool response into a clean dict."""
        if isinstance(raw_result, dict):
            content = raw_result.get("content", [])
            if content and isinstance(content, list) and content[0].get("type") == "text":
                text = content[0].get("text", "")
                try:
                    return json.loads(text)
                except (json.JSONDecodeError, ValueError):
                    return {"raw_text": text}
        return raw_result if isinstance(raw_result, dict) else {"result": raw_result}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def list_tools(self) -> list[dict]:
        """List available MCP tools (cached after first call)."""
        if not self.is_configured():
            return []
        if self._tool_cache is not None:
            return self._tool_cache
        client = await self._get_client()
        tools = await client.list_tools(self.settings.mcp_agent_key)
        self._tool_cache = [
            t if isinstance(t, dict) else t.model_dump() for t in tools
        ]
        return self._tool_cache or []

    async def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """Invoke an MCP tool with automatic retry on transient failures."""
        last_exc: Exception | None = None
        for attempt in range(2):
            try:
                client = await self._get_client()
                result = await client.query_tool(
                    agent_key=self.settings.mcp_agent_key,
                    tool_name=tool_name,
                    arguments=arguments,
                )
                return self._parse_tool_response(result)
            except Exception as exc:
                last_exc = exc
                if attempt == 0:
                    await self._reset_client()
                else:
                    raise
        raise last_exc  # type: ignore[misc]

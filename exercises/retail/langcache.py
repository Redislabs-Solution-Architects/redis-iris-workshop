"""Module 4: LangCache -- open the workshop guide for guidance."""

from __future__ import annotations

from backend.app.bases.langcache_base import LangCacheBase


class LangCacheService(LangCacheBase):
    """Semantic caching for LLM responses."""

    def search_request_body(self, prompt):
        """Replace return None with your search config -- see the workshop guide."""

        return None

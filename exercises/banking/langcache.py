"""Module 4: LangCache -- open the workshop guide for guidance."""

from __future__ import annotations

from backend.app.bases.langcache_base import LangCacheBase


class LangCacheService(LangCacheBase):
    """Semantic caching for LLM responses."""

    def search_request_body(self, prompt):
        """Configure the semantic cache search.

        Return a dict with:
            "prompt": ???,                # the user's query
            "similarityThreshold": ???,   # 0–1, try 0.82
            "searchStrategies": [???],    # "semantic" matches by meaning
        """
        return None  # Replace with your implementation

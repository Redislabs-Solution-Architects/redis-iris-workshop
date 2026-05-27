"""Module 3: LangCache — Reference Solution."""

from backend.app.bases.langcache_base import LangCacheBase


class LangCacheService(LangCacheBase):

    def search_request_body(self, prompt):
        return {
            "prompt": prompt,
            "similarityThreshold": 0.82,
            "searchStrategies": ["semantic"],
        }

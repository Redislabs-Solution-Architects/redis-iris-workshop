"""Module 5: Agent Memory — Reference Solution."""

from backend.app.bases.memory_base import MemoryBase, sanitize_owner_id


class MemoryService(MemoryBase):

    def long_term_search_payload(self, *, text, owner_id, session_id, limit):
        return {
            "text": text,
            "similarityThreshold": 0.2,
            "filterOp": "all",
            "limit": limit or 5,
            "filter": {
                "ownerId": {"eq": sanitize_owner_id(owner_id)},
                "namespace": {"eq": "digital-native-demo"},
            },
        }

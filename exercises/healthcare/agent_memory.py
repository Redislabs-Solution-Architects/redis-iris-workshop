"""Module 5: Agent Memory -- open the workshop guide for guidance."""

from __future__ import annotations

from backend.app.bases.memory_base import MemoryBase, sanitize_owner_id


class MemoryService(MemoryBase):
    """Session memory and long-term memory for the support agent."""

    def long_term_search_payload(self, *, text, owner_id, session_id, limit):
        """Configure the long-term memory search.

        Return a dict with:
            "text": ???,                  # the search query
            "similarityThreshold": ???,   # 0–1, try 0.2
            "filterOp": ???,              # "all" means every filter must match
            "limit": ???,                 # how many memories to return
            "filter": {                   # scope to this user and app
                "ownerId": {"eq": ???},   # use sanitize_owner_id(owner_id)
                "namespace": {"eq": ???}, # "healthcare-demo"
            },
        }
        """
        return None  # Replace with your implementation

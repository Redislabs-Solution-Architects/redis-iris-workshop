"""Module 5: Agent Memory -- open the workshop guide for guidance."""

from __future__ import annotations

from backend.app.bases.memory_base import MemoryBase, sanitize_owner_id


class MemoryService(MemoryBase):
    """Session memory and long-term memory for the support agent."""

    def long_term_search_payload(self, *, text, owner_id, session_id, limit):
        """Replace return None with your search payload -- see the workshop guide."""

        return None

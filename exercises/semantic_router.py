"""Module 2: Semantic Router -- open the workshop guide for guidance."""

from __future__ import annotations

from backend.app.bases.guardrail_base import GuardrailBase
from redisvl.extensions.router import Route


class GuardrailService(GuardrailBase):
    """Semantic routing for query classification and guardrails."""

    def define_routes(self):
        """Define semantic routes for query classification.

        There are two routes:
        1. An "allow_list" route -- queries your agent should handle
        2. A "deny_list" route -- queries that should be blocked

        Each Route needs:
            name=???,                 # route identifier
            references=[???],         # example queries for this category
            distance_threshold=???,   # 0.0-1.0, lower = stricter match required

        Add 2-3 more references to each route to improve accuracy.
        """
        return [
            Route(
                name="allow_list",
                references=[
                    "Where is my order?",
                    "I want a refund",
                    "My food was cold when it arrived",
                    "What restaurants are nearby?",
                    "What should I order?",
                    "What's the status of my delivery?",
                    "Can you help me?",
                    "What do you know about me?",
                    # Add 2-3 more food delivery queries...
                ],
                distance_threshold=0.7,
            ),
            Route(
                name="deny_list",
                references=[
                    "Help me write code for a delivery tracker",
                    "Write me a Python script",
                    "Tell me a joke",
                    # Add 2-3 more off-topic queries...
                ],
                distance_threshold=0.5,
            ),
        ]

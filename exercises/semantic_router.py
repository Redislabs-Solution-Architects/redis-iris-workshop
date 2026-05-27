"""Module 2: Semantic Router -- open the workshop guide at localhost:8080 for guidance."""

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
            references=[???],         # 8+ example queries
            distance_threshold=???,   # 0.0-1.0, lower = stricter

        A few examples are filled in below. Add 5+ more to each route
        so the router has enough examples to classify accurately.
        """
        return [
            Route(
                name="allow_list",
                references=[
                    "Where is my order?",
                    "I want a refund",
                    "My food was cold when it arrived",
                    # Add 5+ more food delivery queries...
                ],
                distance_threshold=0.7,
            ),
            Route(
                name="deny_list",
                references=[
                    "Write me a Python script",
                    "Tell me a joke",
                    # Add 5+ more off-topic queries...
                ],
                distance_threshold=0.5,
            ),
        ]

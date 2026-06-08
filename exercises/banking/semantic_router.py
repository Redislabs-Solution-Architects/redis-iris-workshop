"""Module 2: Semantic Router -- open the workshop guide for guidance."""

from __future__ import annotations

from backend.app.bases.guardrail_base import GuardrailBase
from redisvl.extensions.router import Route


class GuardrailService(GuardrailBase):
    """Semantic routing for query classification and guardrails."""

    def define_routes(self):
        """Define semantic routes for query classification.

        There are two routes:
        1. A "banking" route -- queries your agent should handle
        2. An "off_topic" route -- queries that should be blocked

        Each Route needs:
            name=???,                 # route identifier
            references=[???],         # example queries for this category
            distance_threshold=???,   # 0.0-1.0, lower = stricter match required

        Add 2-3 more references to each route to improve accuracy.
        """
        return [
            Route(
                name="banking",
                references=[
                    "What are my account balances?",
                    "Fixed deposit rate FD6",
                    "Waive annual card fee",
                    "Branch hours Tampines",
                    "What accounts do I have?",
                    "Early withdrawal penalty",
                    "Can you help me?",
                    "What do you know about me?",
                    # Add 2-3 more banking queries...
                ],
                distance_threshold=0.7,
            ),
            Route(
                name="off_topic",
                references=[
                    "Why is the sky blue?",
                    "Tell me a joke",
                    "How do I cook pasta?",
                    # Add 2-3 more off-topic queries...
                ],
                distance_threshold=0.5,
            ),
        ]

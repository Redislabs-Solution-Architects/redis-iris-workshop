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
                    "Show me my appointment calendar",
                    "When is my next appointment?",
                    "I need an update on my referral",
                    "Who is my primary care provider?",
                    "Is telehealth available for my visit?",
                    "What's my insurance status?",
                    "Can you help me?",
                    "What do you know about me?",
                    # Add 2-3 more healthcare queries...
                ],
                distance_threshold=0.7,
            ),
            Route(
                name="deny_list",
                references=[
                    "Write me a Python script",
                    "Tell me a joke",
                    "What's the weather like today?",
                    # Add 2-3 more off-topic queries...
                ],
                distance_threshold=0.5,
            ),
        ]

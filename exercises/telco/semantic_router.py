"""Module 2: Semantic Router -- open the workshop guide for guidance."""

from __future__ import annotations

from backend.app.bases.guardrail_base import GuardrailBase
from redisvl.extensions.router import Route


class GuardrailService(GuardrailBase):
    """Semantic routing for query classification and guardrails."""

    def define_routes(self):
        """Define semantic routes for query classification.

        There are two routes:
        1. A "allow_list" route -- queries your agent should handle
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
                    "Why is my bill so high this month?",
                    "How do I upgrade my phone?",
                    "What plans do you offer?",
                    "Set up autopay",
                    "Do I have device insurance?",
                    "I have no signal at home",
                    "Can you help me?",
                    "What do you know about my preferences?",
                    # Add 2-3 more wireless support queries...
                ],
                distance_threshold=0.7,
            ),
            Route(
                name="deny_list",
                references=[
                    "What's the weather like today?",
                    "Tell me a joke",
                    "Help me with my homework",
                    # Add 2-3 more off-topic queries...
                ],
                distance_threshold=0.5,
            ),
        ]

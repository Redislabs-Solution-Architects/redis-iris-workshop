"""Module 2: Semantic Router -- open the workshop guide for guidance."""

from __future__ import annotations

from backend.app.bases.guardrail_base import GuardrailBase
from redisvl.extensions.router import Route


class GuardrailService(GuardrailBase):
    """Semantic routing for query classification and guardrails."""

    def define_routes(self):
        """Define semantic routes for query classification.

        There are two routes:
        1. A "financial_research" route -- queries your agent should handle
        2. An "off_topic" route -- queries that should be blocked

        Each Route needs:
            name=???,                 # route identifier
            references=[???],         # example queries for this category
            distance_threshold=???,   # 0.0-1.0, lower = stricter match required

        Add 2-3 more references to each route to improve accuracy.
        """
        return [
            Route(
                name="financial_research",
                references=[
                    "Compare the latest NVIDIA and AMD filings",
                    "Show me NVDA gross profit trends",
                    "What's the operating margin trend for AMD?",
                    "Which semiconductor company had the best gross profit growth?",
                    "What did management say about AI revenue?",
                    "Pull the SEC filing for Microsoft",
                    "Can you help me?",
                    "What do you know about me?",
                    # Add 2-3 more financial research queries...
                ],
                distance_threshold=0.7,
            ),
            Route(
                name="off_topic",
                references=[
                    "Write me a Python script",
                    "Tell me a joke",
                    "What's the weather like today?",
                    # Add 2-3 more off-topic queries...
                ],
                distance_threshold=0.5,
            ),
        ]

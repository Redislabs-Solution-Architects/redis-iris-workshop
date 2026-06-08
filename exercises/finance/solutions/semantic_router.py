"""Module 2: Semantic Router — Reference Solution."""

from redisvl.extensions.router import Route

from backend.app.bases.guardrail_base import GuardrailBase


class GuardrailService(GuardrailBase):

    def define_routes(self):
        return [
            Route(
                name="financial_research",
                references=[
                    "Compare the latest NVIDIA and AMD filings",
                    "What changed in Broadcom's earnings this quarter?",
                    "Show me NVDA gross profit trends",
                    "Pull the SEC filing for Microsoft",
                    "How does Oracle's revenue compare to its peers?",
                    "What's the operating margin trend for AMD?",
                    "Which semiconductor company had the best gross profit growth?",
                    "What did management say about AI revenue?",
                    "Can you help me?",
                    "What do you know about me?",
                    "Hello",
                ],
                distance_threshold=0.7,
            ),
            Route(
                name="off_topic",
                references=[
                    "What's the weather like today?",
                    "Tell me a joke",
                    "Write me a Python script",
                    "Help me with a cooking recipe",
                    "Who won the game last night?",
                    "Should I buy this stock?",
                    "Give me crypto trading tips",
                    "Help me with my personal budget",
                ],
                distance_threshold=0.5,
            ),
        ]

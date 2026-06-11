"""Module 2: Semantic Router — Reference Solution."""

from redisvl.extensions.router import Route

from backend.app.bases.guardrail_base import GuardrailBase


class GuardrailService(GuardrailBase):

    def define_routes(self):
        return [
            Route(
                name="allow_list",
                references=[
                    "Check my savings balance",
                    "What are my account balances?",
                    "Fixed deposit rate FD6",
                    "Waive annual card fee",
                    "Branch hours Tampines",
                    "What accounts do I have?",
                    "Early withdrawal penalty",
                    "Place 2000 SGD in the 6-month FD",
                    "Show me my service request history",
                    "Remember my preferences",
                    "Can you help me?",
                    "What do you know about me?",
                    "Hello",
                ],
                distance_threshold=0.7,
            ),
            Route(
                name="deny_list",
                references=[
                    "Why is the sky blue?",
                    "Who is the current US president?",
                    "Recipe for chocolate cake",
                    "Capital of Mongolia",
                    "Write me a Python sorting algorithm",
                    "Tell me a joke",
                    "How do I cook pasta?",
                    "Help me with my homework",
                ],
                distance_threshold=0.5,
            ),
        ]

"""Module 2: Semantic Router — Reference Solution."""

from redisvl.extensions.router import Route

from backend.app.bases.guardrail_base import GuardrailBase


class GuardrailService(GuardrailBase):

    def define_routes(self):
        return [
            Route(
                name="allow_list",
                references=[
                    "Where is my order?",
                    "I want a refund",
                    "My food was cold when it arrived",
                    "What restaurants are nearby?",
                    "Recommend me something to eat",
                    "What's the status of my delivery?",
                    "Can you help me?",
                    "What do you know about me?",
                    "My order is late",
                    "What's your refund policy?",
                    "Save my delivery preferences",
                    "Hello",
                ],
                distance_threshold=0.7,
            ),
            Route(
                name="deny_list",
                references=[
                    "Help me write code for a delivery tracker",
                    "Write me a Python script",
                    "Tell me a joke",
                    "What's the weather like today?",
                    "Help me with my homework",
                    "Who won the Super Bowl?",
                    "Explain quantum physics",
                    "How do I fix my car?",
                ],
                distance_threshold=0.5,
            ),
        ]

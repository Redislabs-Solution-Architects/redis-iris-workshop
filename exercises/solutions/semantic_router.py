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
                    "What's the status of my delivery?",
                    "My order is late",
                    "I want a refund",
                    "My food was cold when it arrived",
                    "What's your refund policy?",
                    "What restaurants are nearby?",
                    "What do you know about me?",
                    "Hello",
                    "Can you help me?",
                ],
                distance_threshold=0.7,
            ),
            Route(
                name="deny_list",
                references=[
                    "What's the weather like today?",
                    "Write me a Python script",
                    "Help me with my homework",
                    "Tell me a joke",
                    "Who won the Super Bowl?",
                    "Explain quantum physics",
                    "How do I fix my car?",
                    "Generate an image of a cat",
                ],
                distance_threshold=0.5,
            ),
        ]

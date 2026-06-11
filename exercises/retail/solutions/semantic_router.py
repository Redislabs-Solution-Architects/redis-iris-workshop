"""Module 2: Semantic Router — Reference Solution."""

from redisvl.extensions.router import Route

from backend.app.bases.guardrail_base import GuardrailBase


class GuardrailService(GuardrailBase):

    def define_routes(self):
        return [
            Route(
                name="allow_list",
                references=[
                    "What laptops do you have in stock?",
                    "I'm looking for a gaming PC",
                    "Do you carry any smart home devices?",
                    "What's the price of this TV?",
                    "Can I pick that up at my local store?",
                    "When will my order arrive?",
                    "What's your return policy?",
                    "Compare these two laptops",
                    "Is this available for curbside pickup?",
                    "What's on sale right now?",
                    "Can you help me?",
                    "What do you know about me?",
                    "Remember my preferences",
                    "Hello",
                ],
                distance_threshold=0.7,
            ),
            Route(
                name="deny_list",
                references=[
                    "What's the weather like today?",
                    "Tell me a joke",
                    "Write me a Python script",
                    "Help me with my homework",
                    "Who won the Super Bowl?",
                    "Explain quantum physics",
                    "Help me debug my code",
                    "How do I cook pasta?",
                ],
                distance_threshold=0.5,
            ),
        ]

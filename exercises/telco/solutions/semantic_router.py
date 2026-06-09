"""Module 2: Semantic Router — Reference Solution."""

from redisvl.extensions.router import Route

from backend.app.bases.guardrail_base import GuardrailBase


class GuardrailService(GuardrailBase):

    def define_routes(self):
        return [
            Route(
                name="wireless_support",
                references=[
                    "Why is my bill so high this month?",
                    "What's this charge on my bill?",
                    "Set up autopay",
                    "I need a payment extension",
                    "How do I upgrade my phone?",
                    "I want to trade in my phone",
                    "Do I have device insurance?",
                    "How do I unlock my phone?",
                    "What plans do you offer?",
                    "I want to change my plan",
                    "How much data have I used?",
                    "Do you have international plans?",
                    "I have no signal at home",
                    "Can you help me?",
                    "What do you know about my preferences?",
                    "Hello",
                ],
                distance_threshold=0.7,
            ),
            Route(
                name="off_topic",
                references=[
                    "What's the weather like today?",
                    "Write me a Python script",
                    "Help me with my homework",
                    "Tell me a joke",
                    "Who won the Super Bowl?",
                    "Explain quantum physics",
                    "Write a poem about love",
                    "Who is the president?",
                    "Translate this to Spanish",
                    "Help me debug my code",
                ],
                distance_threshold=0.5,
            ),
        ]

"""Module 2: Semantic Router — Reference Solution."""

from redisvl.extensions.router import Route

from backend.app.bases.guardrail_base import GuardrailBase


class GuardrailService(GuardrailBase):

    def define_routes(self):
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
                    "I need to schedule a follow-up",
                    "Can I reschedule my appointment?",
                    "Remember my preferences",
                    "Hello",
                ],
                distance_threshold=0.7,
            ),
            Route(
                name="deny_list",
                references=[
                    "Write me a Python script",
                    "Tell me a joke",
                    "What's the weather like today?",
                    "Help me with my homework",
                    "Who won the Super Bowl?",
                    "Explain quantum physics",
                    "Help me debug my code",
                    "How do I fix my car?",
                ],
                distance_threshold=0.5,
            ),
        ]

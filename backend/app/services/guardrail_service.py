import os as _os

if _os.getenv("USE_SOLUTIONS"):
    from exercises.solutions.semantic_router import GuardrailService  # noqa: F401
else:
    from exercises.semantic_router import GuardrailService  # noqa: F401

import os as _os

if _os.getenv("USE_SOLUTIONS"):
    from exercises.solutions.context_retriever import ContextSurfaceService  # noqa: F401
else:
    from exercises.context_retriever import ContextSurfaceService  # noqa: F401

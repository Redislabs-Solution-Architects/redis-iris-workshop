import os as _os

if _os.getenv("USE_SOLUTIONS"):
    from exercises.solutions.vector_search import SimpleRAGService  # noqa: F401
else:
    from exercises.vector_search import SimpleRAGService  # noqa: F401

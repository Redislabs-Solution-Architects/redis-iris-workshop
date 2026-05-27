import os as _os

if _os.getenv("USE_SOLUTIONS"):
    from exercises.solutions.agent_memory import MemoryService  # noqa: F401
else:
    from exercises.agent_memory import MemoryService  # noqa: F401

from backend.app.bases.memory_base import sanitize_owner_id  # noqa: F401

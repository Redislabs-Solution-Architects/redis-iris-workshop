import importlib
import os as _os

_domain = _os.getenv("DEMO_DOMAIN") or "digital-native"
_use_solutions = _os.getenv("USE_SOLUTIONS", "")

if _use_solutions:
    _mod = importlib.import_module(f"exercises.{_domain}.solutions.agent_memory")
else:
    _mod = importlib.import_module(f"exercises.{_domain}.agent_memory")

MemoryService = _mod.MemoryService  # noqa: F401

from backend.app.bases.memory_base import sanitize_owner_id  # noqa: E402, F401

import importlib
import os as _os

_domain = _os.getenv("DEMO_DOMAIN") or "digital-native"
_use_solutions = _os.getenv("USE_SOLUTIONS", "")

if _use_solutions:
    _mod = importlib.import_module(f"exercises.{_domain}.solutions.vector_search")
else:
    _mod = importlib.import_module(f"exercises.{_domain}.vector_search")

SimpleRAGService = _mod.SimpleRAGService  # noqa: F401

import importlib
import os as _os

_domain = _os.getenv("DEMO_DOMAIN") or "reddash"
_use_solutions = _os.getenv("USE_SOLUTIONS", "")

if _use_solutions:
    _mod = importlib.import_module(f"exercises.{_domain}.solutions.semantic_router")
else:
    _mod = importlib.import_module(f"exercises.{_domain}.semantic_router")

GuardrailService = _mod.GuardrailService  # noqa: F401

import importlib
import os as _os

_domain = _os.getenv("DEMO_DOMAIN") or "digital-native"
_use_solutions = _os.getenv("USE_SOLUTIONS", "")

if _use_solutions:
    _mod = importlib.import_module(f"exercises.{_domain}.solutions.langcache")
else:
    _mod = importlib.import_module(f"exercises.{_domain}.langcache")

LangCacheService = _mod.LangCacheService  # noqa: F401

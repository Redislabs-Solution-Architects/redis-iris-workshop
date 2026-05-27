import os as _os

if _os.getenv("USE_SOLUTIONS"):
    from exercises.solutions.langcache import LangCacheService  # noqa: F401
else:
    from exercises.langcache import LangCacheService  # noqa: F401

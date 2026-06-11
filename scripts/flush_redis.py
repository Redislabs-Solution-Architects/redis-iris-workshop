"""Flush all Redis keys except memory:* (preserves Agent Memory data)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.redis_connection import create_redis_client
from backend.app.settings import get_settings

settings = get_settings()
r = create_redis_client(settings)

cursor, deleted, preserved = 0, 0, 0
while True:
    cursor, keys = r.scan(cursor=cursor, count=500)
    if keys:
        keep = [k for k in keys if (k if isinstance(k, str) else k.decode()).startswith("memory:")]
        drop = [k for k in keys if k not in keep]
        if drop:
            r.delete(*drop)
            deleted += len(drop)
        preserved += len(keep)
    if cursor == 0:
        break

print(f"Flushed Redis at {settings.redis_host}:{settings.redis_port}/{settings.redis_db}")
print(f"  Deleted {deleted} keys, preserved {preserved} memory keys")

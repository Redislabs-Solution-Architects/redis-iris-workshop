"""Seed LangCache with a pre-filled entry for the workshop.

Usage:
    uv run python -m scripts.seed_langcache
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.services.langcache_service import LangCacheService
from backend.app.settings import get_settings

SEED_ENTRIES = [
    {
        "prompt": "What's your refund policy for late deliveries?",
        "response": (
            "If your order is delivered more than **15 minutes late**, you get a "
            "**20% credit** on your next order. If it's over **30 minutes late**, you can "
            "request a **refund of the delivery fee**; if it's over **45 minutes late**, "
            "you may qualify for a **full order refund**. Please contact support with your "
            "order details to start the process."
        ),
        "attributes": {"industry": "food-delivery", "mode": "context_surfaces", "user_id": "demo"},
    },
]


async def main() -> None:
    settings = get_settings()
    service = LangCacheService(settings)

    if not service.is_configured():
        print("LangCache is not configured.")
        print("Set LANGCACHE_HOST, LANGCACHE_CACHE_ID, and LANGCACHE_API_KEY in .env")
        sys.exit(1)

    print(f"Seeding {len(SEED_ENTRIES)} entries...")
    for entry in SEED_ENTRIES:
        ok = await service.store(
            prompt=entry["prompt"],
            response=entry["response"],
            attributes=entry.get("attributes"),
        )
        status = "OK" if ok else "FAILED"
        print(f"  [{status}] {entry['prompt'][:60]}")

    await service.close()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())

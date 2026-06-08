"""Seed LangCache with pre-filled entries from the domain config.

Usage:
    uv run python -m scripts.seed_langcache
    uv run python -m scripts.seed_langcache --domain healthcare
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.core.domain_loader import load_domain
from backend.app.services.langcache_service import LangCacheService
from backend.app.settings import get_settings


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", default=os.getenv("DEMO_DOMAIN") or "reddash")
    args = parser.parse_args()

    settings = get_settings()
    domain = load_domain(args.domain)
    service = LangCacheService(settings)

    if not service.has_credentials():
        print("LangCache is not configured.")
        print("Set LANGCACHE_HOST, LANGCACHE_CACHE_ID, and LANGCACHE_API_KEY in .env")
        sys.exit(1)

    seed_entries = domain.manifest.seed_langcache
    if not seed_entries:
        print(f"No seed langcache entries defined for domain '{args.domain}'.")
        return

    print(f"Domain: {args.domain}")
    print(f"Seeding {len(seed_entries)} entries...")
    for entry in seed_entries:
        try:
            ok = await service.store(
                prompt=entry.prompt,
                response=entry.response,
                attributes=entry.attributes or None,
            )
            status = "OK" if ok else "FAILED"
        except Exception as exc:
            ok = False
            status = f"ERROR: {exc}"
        print(f"  [{status}] {entry.prompt[:60]}")

    await service.close()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())

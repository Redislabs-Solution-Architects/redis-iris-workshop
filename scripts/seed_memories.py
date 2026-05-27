"""Seed long-term memories for the workshop demo customer.

Clears existing memories, then seeds two pre-defined memories.

Usage:
    uv run python -m scripts.seed_memories
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.settings import get_settings

SEED_MEMORIES = [
    {
        "text": "Prefers contactless delivery",
        "memory_type": "semantic",
        "topics": ["delivery", "preferences"],
    },
    {
        "text": "Likes spicy food",
        "memory_type": "semantic",
        "topics": ["food", "preferences"],
    },
]


def main() -> None:
    settings = get_settings()
    service = MemoryService(settings)

    if not service.is_configured():
        print("Memory service is not configured.")
        print("Set MEMORY_API_BASE_URL, MEMORY_STORE_ID, and MEMORY_API_KEY in .env")
        sys.exit(1)

    owner_id = settings.memory_owner_id or "CUST_DEMO_001"
    print(f"Owner: {owner_id}")

    print("Searching for existing long-term memories...")
    import httpx

    base = settings.memory_api_base_url.rstrip("/")
    store_id = settings.memory_store_id
    api_key = settings.memory_api_key
    if not api_key.lower().startswith(("bearer ", "basic ")):
        api_key = f"Bearer {api_key}"

    headers = {
        "Authorization": api_key,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    namespace = settings.memory_namespace.strip() or "reddash-demo"

    with httpx.Client(timeout=30.0) as client:
        search_resp = client.post(
            f"{base}/v1/stores/{store_id}/long-term-memory/search",
            headers=headers,
            json={
                "text": "*",
                "similarityThreshold": 0.0,
                "filterOp": "all",
                "limit": 50,
                "filter": {
                    "ownerId": {"eq": owner_id},
                    "namespace": {"eq": namespace},
                },
            },
        )
        if search_resp.status_code < 400:
            body = search_resp.json()
            existing = body.get("items") or body.get("memories") or []
        else:
            existing = []

        if existing:
            print(f"  Found {len(existing)} existing memories, deleting...")
            for mem in existing:
                mid = mem.get("id")
                if mid:
                    try:
                        client.request(
                            "DELETE",
                            f"{base}/v1/stores/{store_id}/long-term-memory",
                            headers=headers,
                            json={"memoryIds": [mid]},
                        )
                        print(f"  Deleted: {mid}")
                    except Exception as e:
                        print(f"  Failed to delete {mid}: {e}")
        else:
            print("  No existing memories found.")

        print(f"Seeding {len(SEED_MEMORIES)} memories...")
        import uuid
        for entry in SEED_MEMORIES:
            from backend.app.services.memory_service import sanitize_owner_id
            payload = {
                "memories": [
                    {
                        "id": str(uuid.uuid4()),
                        "text": entry["text"],
                        "memoryType": entry["memory_type"],
                        "ownerId": sanitize_owner_id(owner_id),
                        "namespace": namespace,
                        "topics": entry["topics"],
                    }
                ]
            }
            resp = client.post(
                f"{base}/v1/stores/{store_id}/long-term-memory",
                headers=headers,
                json=payload,
            )
            if resp.status_code < 400:
                print(f"  Seeded: {entry['text']!r}")
            else:
                print(f"  FAILED: {entry['text']!r} -> {resp.status_code}: {resp.text}")

    print("Done.")


if __name__ == "__main__":
    main()

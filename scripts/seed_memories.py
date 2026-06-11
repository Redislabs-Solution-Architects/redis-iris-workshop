"""Seed long-term memories for the workshop demo customer.

Clears existing memories, then seeds memories defined in the domain config.

Usage:
    uv run python -m scripts.seed_memories
    uv run python -m scripts.seed_memories --domain healthcare
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx

from backend.app.core.domain_loader import load_domain
from backend.app.redis_connection import create_redis_client
from backend.app.services.memory_service import MemoryService
from backend.app.bases.memory_base import sanitize_owner_id
from backend.app.settings import get_settings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", default=os.getenv("DEMO_DOMAIN") or "digital-native")
    args = parser.parse_args()

    settings = get_settings()
    domain = load_domain(args.domain)
    service = MemoryService(settings)

    if not service.has_credentials():
        print("Memory service is not configured.")
        print("Set MEMORY_API_BASE_URL, MEMORY_STORE_ID, and MEMORY_API_KEY in .env")
        sys.exit(1)

    seed_memories = domain.manifest.seed_memories
    if not seed_memories:
        print(f"No seed memories defined for domain '{args.domain}'.")
        return

    owner_id = settings.memory_owner_id or domain.manifest.identity.default_id
    namespace = settings.memory_namespace.strip() or f"{args.domain}-demo"
    print(f"Domain: {args.domain}")
    print(f"Owner: {owner_id}")
    print(f"Namespace: {namespace}")

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

    with httpx.Client(timeout=30.0) as client:
        print("Searching for existing long-term memories...")
        search_resp = client.post(
            f"{base}/v1/stores/{store_id}/long-term-memory/search",
            headers=headers,
            json={
                "text": "*",
                "similarityThreshold": 0.0,
                "filterOp": "all",
                "limit": 50,
                "filter": {
                    "ownerId": {"eq": sanitize_owner_id(owner_id)},
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

        print(f"Seeding {len(seed_memories)} memories...")
        for entry in seed_memories:
            payload = {
                "memories": [
                    {
                        "id": str(uuid.uuid4()),
                        "text": entry.text,
                        "memoryType": entry.memory_type,
                        "ownerId": sanitize_owner_id(owner_id),
                        "namespace": namespace,
                        "topics": entry.topics,
                    }
                ]
            }
            resp = client.post(
                f"{base}/v1/stores/{store_id}/long-term-memory",
                headers=headers,
                json=payload,
            )
            if resp.status_code < 400:
                print(f"  Seeded: {entry.text!r}")
            else:
                print(f"  FAILED: {entry.text!r} -> {resp.status_code}: {resp.text}")

    _ensure_memory_index(settings)
    print("Done.")


def _ensure_memory_index(settings) -> None:
    """Ensure the Memory API's FT search index exists on the backing Redis.

    The Memory API stores data in our Redis Cloud database. A FLUSHDB or
    eviction can destroy the index; we recreate it so search works.
    """
    store_id = settings.memory_store_id
    if not store_id:
        return
    index_name = f"memory:{store_id}:ltm"
    prefix = f"memory:{store_id}:ltm:"
    r = create_redis_client(settings)
    try:
        r.execute_command("FT.INFO", index_name)
        return
    except Exception:
        pass
    print(f"  Recreating memory search index '{index_name}'...")
    try:
        r.execute_command(
            "FT.CREATE", index_name,
            "ON", "HASH",
            "PREFIX", "1", prefix,
            "SCHEMA",
            "text", "TEXT",
            "owner_id", "TAG",
            "namespace", "TAG",
            "memory_type", "TAG",
            "topics", "TAG", "SEPARATOR", ",",
            "session_id", "TAG",
            "id", "TAG",
            "created_at", "NUMERIC",
            "updated_at", "NUMERIC",
            "text_vector", "VECTOR", "HNSW", "6",
            "TYPE", "FLOAT32",
            "DIM", "3072",
            "DISTANCE_METRIC", "COSINE",
        )
        print("  Index created.")
    except Exception as e:
        print(f"  Index creation failed: {e}")


if __name__ == "__main__":
    main()

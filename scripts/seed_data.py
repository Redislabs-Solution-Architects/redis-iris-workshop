"""Seed policy documents into Redis for Simple RAG (Module 0/1).

Loads pre-generated policies.jsonl into Redis as JSON documents and
creates a RediSearch vector index on the content_embedding field.

This uses redis-py directly — no Context Surfaces SDK needed.

Usage:
    uv run python scripts/seed_data.py --domain reddash
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.redis_connection import create_redis_client
from backend.app.settings import get_settings


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", default="reddash")
    args = parser.parse_args()

    settings = get_settings()

    if not settings.redis_host or not settings.redis_password:
        print("Redis is not configured. Set REDIS_HOST and REDIS_PASSWORD in .env")
        sys.exit(1)

    client = create_redis_client(settings)

    try:
        client.ping()
    except Exception as exc:
        print(f"Cannot connect to Redis: {exc}")
        sys.exit(1)

    output_dir = Path(__file__).resolve().parents[1] / "output" / args.domain
    policies_file = output_dir / "policies.jsonl"

    if not policies_file.exists():
        print(f"File not found: {policies_file}")
        print("The pre-generated data should be in the output/ directory.")
        sys.exit(1)

    prefix = f"{args.domain}_policy"
    index_name = f"idx:{prefix}"

    print(f"Loading policies from {policies_file}...")
    policies = []
    with open(policies_file) as f:
        for line in f:
            line = line.strip()
            if line:
                policies.append(json.loads(line))

    print(f"  Found {len(policies)} policy documents")

    loaded = 0
    for policy in policies:
        policy_id = policy.get("policy_id", f"policy_{loaded}")
        key = f"{prefix}:{policy_id}"

        doc = {}
        embedding = None
        for field_name, value in policy.items():
            if field_name == "content_embedding":
                embedding = value
            else:
                doc[field_name] = value

        client.json().set(key, "$", doc)

        if embedding:
            import struct
            blob = struct.pack(f"{len(embedding)}f", *embedding)
            client.json().set(key, "$.content_embedding", list(embedding))

        loaded += 1

    print(f"  Loaded {loaded} documents into Redis")

    try:
        client.execute_command("FT.DROPINDEX", index_name)
        print(f"  Dropped existing index: {index_name}")
    except Exception:
        pass

    vector_dim = 1536
    for policy in policies:
        emb = policy.get("content_embedding", [])
        if emb:
            vector_dim = len(emb)
            break

    return_fields = ["title", "category", "content"]

    schema_parts = [
        "$.policy_id", "AS", "policy_id", "TAG",
        "$.title", "AS", "title", "TEXT", "WEIGHT", "2.0",
        "$.category", "AS", "category", "TAG",
        "$.content", "AS", "content", "TEXT",
        "$.content_embedding", "AS", "content_embedding", "VECTOR", "FLAT", "6",
        "TYPE", "FLOAT32", "DIM", str(vector_dim), "DISTANCE_METRIC", "COSINE",
    ]

    client.execute_command(
        "FT.CREATE", index_name,
        "ON", "JSON",
        "PREFIX", "1", f"{prefix}:",
        "SCHEMA", *schema_parts,
    )
    print(f"  Created vector index: {index_name}")

    meta_key = f"{args.domain}:meta:dataset"
    client.delete(meta_key)
    client.hset(meta_key, mapping={"policies": str(loaded)})
    print(f"  Set dataset meta: {meta_key}")

    print("\nDone! Policy data is ready for Simple RAG.")
    print("Run `make dev` and try asking a policy question.")


if __name__ == "__main__":
    main()

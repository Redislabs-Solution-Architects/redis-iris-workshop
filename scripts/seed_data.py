"""Seed RAG documents into Redis for Module 1 (Vector Search).

Loads the domain-specific document file (policies, guides, health docs, etc.)
into Redis as JSON documents and creates a RediSearch vector index on the
content_embedding field.

This uses redis-py directly — no Context Surfaces SDK needed.

Usage:
    uv run python scripts/seed_data.py --domain digital-native
"""

from __future__ import annotations

import argparse
import json
import os
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.app.redis_connection import create_redis_client
from backend.app.settings import get_settings

DOMAIN_RAG_CONFIG: dict[str, dict] = {
    "digital-native": {
        "file": "policies.jsonl",
        "id_field": "policy_id",
        "key_prefix": "reddash_policy",
        "index_name": "idx:reddash_policy",
        "text_fields": {
            "title": {"type": "TEXT", "weight": 2.0},
            "category": {"type": "TAG"},
            "content": {"type": "TEXT"},
        },
        "return_fields": ["title", "category", "content", "policy_id"],
    },
    "banking": {
        "file": "bank_documents.jsonl",
        "id_field": "document_id",
        "key_prefix": "radish_bank_document",
        "index_name": "idx:radish_bankdocument",
        "text_fields": {
            "title": {"type": "TEXT", "weight": 2.0},
            "category": {"type": "TAG"},
            "content": {"type": "TEXT"},
        },
        "return_fields": ["title", "category", "content", "document_id"],
    },
    "healthcare": {
        "file": "healthdocs.jsonl",
        "id_field": "doc_id",
        "key_prefix": "healthcare_healthdoc",
        "index_name": "idx:healthcare_healthdoc",
        "text_fields": {
            "title": {"type": "TEXT", "weight": 2.0},
            "category": {"type": "TAG"},
            "content": {"type": "TEXT"},
        },
        "return_fields": ["title", "category", "content", "doc_id"],
    },
    "retail": {
        "file": "guides.jsonl",
        "id_field": "guide_id",
        "key_prefix": "electrohub_guide",
        "index_name": "idx:electrohub_guide",
        "text_fields": {
            "title": {"type": "TEXT", "weight": 2.0},
            "category": {"type": "TAG"},
            "content": {"type": "TEXT"},
        },
        "return_fields": ["title", "category", "content", "guide_id"],
    },
    "finance": {
        "file": "research_chunks.jsonl",
        "id_field": "chunk_id",
        "key_prefix": "finance_researcher_research_chunk",
        "index_name": "idx:finance_researcher_researchchunk",
        "text_fields": {
            "company_id": {"type": "TAG"},
            "ticker": {"type": "TAG"},
            "document_id": {"type": "TAG"},
            "section_heading": {"type": "TEXT", "weight": 2.0},
            "page_label": {"type": "TAG"},
            "chunk_text": {"type": "TEXT"},
        },
        "return_fields": [
            "company_id", "ticker", "document_id",
            "section_heading", "page_label", "chunk_text", "chunk_id",
        ],
    },
    "telco": {
        "file": "policy_docs.jsonl",
        "id_field": "doc_id",
        "key_prefix": "rmobile_policy_doc",
        "index_name": "idx:rmobile_policydoc",
        "text_fields": {
            "title": {"type": "TEXT", "weight": 2.0},
            "category": {"type": "TAG"},
            "content": {"type": "TEXT"},
        },
        "return_fields": ["title", "category", "content", "doc_id"],
    },
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", default=os.getenv("DEMO_DOMAIN") or "digital-native")
    args = parser.parse_args()

    cfg = DOMAIN_RAG_CONFIG.get(args.domain)
    if cfg is None:
        print(f"Unknown domain: {args.domain}")
        print(f"Available: {', '.join(DOMAIN_RAG_CONFIG)}")
        sys.exit(1)

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
    doc_file = output_dir / cfg["file"]

    if not doc_file.exists():
        print(f"File not found: {doc_file}")
        print("The pre-generated data should be in the output/ directory.")
        sys.exit(1)

    prefix = cfg["key_prefix"]
    id_field = cfg["id_field"]
    index_name = cfg["index_name"]

    print(f"Loading documents from {doc_file}...")
    documents = []
    with open(doc_file) as f:
        for line in f:
            line = line.strip()
            if line:
                documents.append(json.loads(line))

    print(f"  Found {len(documents)} documents")

    loaded = 0
    vector_dim = 1536
    for doc_data in documents:
        doc_id = doc_data.get(id_field, f"doc_{loaded}")
        key = f"{prefix}:{doc_id}"

        doc = {}
        embedding = None
        for field_name, value in doc_data.items():
            if field_name == "content_embedding":
                embedding = value
            else:
                doc[field_name] = value

        client.json().set(key, "$", doc)

        if embedding:
            if loaded == 0:
                vector_dim = len(embedding)
            client.json().set(key, "$.content_embedding", list(embedding))

        loaded += 1

    print(f"  Loaded {loaded} documents into Redis")

    try:
        client.execute_command("FT.DROPINDEX", index_name)
        print(f"  Dropped existing index: {index_name}")
    except Exception:
        pass

    schema_parts: list[str] = []
    for field_name, field_cfg in cfg["text_fields"].items():
        schema_parts.extend([f"$.{field_name}", "AS", field_name])
        schema_parts.append(field_cfg["type"])
        if "weight" in field_cfg:
            schema_parts.extend(["WEIGHT", str(field_cfg["weight"])])

    schema_parts.extend([
        f"$.{id_field}", "AS", id_field, "TAG",
        "$.content_embedding", "AS", "content_embedding", "VECTOR", "FLAT", "6",
        "TYPE", "FLOAT32", "DIM", str(vector_dim), "DISTANCE_METRIC", "COSINE",
    ])

    client.execute_command(
        "FT.CREATE", index_name,
        "ON", "JSON",
        "PREFIX", "1", f"{prefix}:",
        "SCHEMA", *schema_parts,
    )
    print(f"  Created vector index: {index_name}")

    meta_key = f"{args.domain}:meta:dataset"
    client.delete(meta_key)
    client.execute_command("JSON.SET", meta_key, "$", json.dumps({"documents": loaded}))
    print(f"  Set dataset meta: {meta_key}")

    print(f"\nDone! {args.domain} RAG documents are ready for Vector Search.")
    print("Run `make dev` and try asking a document question.")


if __name__ == "__main__":
    main()

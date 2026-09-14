"""Load generated JSONL data into the active domain's Context Surface."""

from __future__ import annotations

import argparse
import asyncio
import importlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from context_surfaces import UnifiedClient  # noqa: E402

from backend.app.core.domain_loader import load_domain  # noqa: E402
from backend.app.settings import get_settings  # noqa: E402

# The Context Surfaces API sits behind nginx, which caps request bodies at 1 MB
# and rejects anything larger with a 413 whose body is HTML. The SDK tries to
# parse that as JSON, so the real status surfaces as a confusing
# "JSONDecodeError: Expecting value: line 1 column 1 (char 0)". Batch under the
# cap so it never happens. Entities differ wildly in record size — chunks carry
# embeddings at ~31 KB each, price bars are ~0.2 KB — so batch by bytes, not count.
MAX_IMPORT_BYTES = 750_000


def batch_by_size(
    rows: list[dict[str, Any]], entity: str, max_bytes: int = MAX_IMPORT_BYTES
) -> list[list[dict[str, Any]]]:
    """Split records into batches whose serialized request body stays under the cap."""
    envelope = len(
        json.dumps(
            {
                "entity": entity,
                "records": [],
                "options": {"on_conflict": "overwrite", "on_error": "fail_fast"},
            }
        )
    )
    batches: list[list[dict[str, Any]]] = []
    current: list[dict[str, Any]] = []
    current_bytes = 0
    for row in rows:
        row_bytes = len(json.dumps(row, default=str)) + 1
        if current and current_bytes + row_bytes + envelope > max_bytes:
            batches.append(current)
            current, current_bytes = [], 0
        current.append(row)
        current_bytes += row_bytes
    if current:
        batches.append(current)
    return batches


def load_records(*, output_dir: Path, entity_by_file: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    payloads: dict[str, list[dict[str, Any]]] = {}
    for file_name, entity in entity_by_file.items():
        path = output_dir / file_name
        rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        payloads[entity.class_name] = rows
    return payloads


def load_generated_models(module_name: str, class_names: list[str], file_path: str | None = None) -> dict[str, type]:
    if file_path and "-" in module_name:
        spec = importlib.util.spec_from_file_location(module_name.replace("-", "_"), ROOT / file_path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        else:
            raise ImportError(f"Cannot load generated models from {file_path}")
    else:
        module = importlib.import_module(module_name)
    return {class_name: getattr(module, class_name) for class_name in class_names}


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", default=None)
    args = parser.parse_args()

    settings = get_settings()
    domain = load_domain(args.domain or settings.demo_domain)
    admin_key = settings.ctx_admin_key
    surface_id = settings.ctx_surface_id

    if not admin_key:
        print("CTX_ADMIN_KEY is not set in .env")
        sys.exit(1)
    if not surface_id:
        print("CTX_SURFACE_ID is not set in .env. Run setup first.")
        sys.exit(1)

    entity_specs = domain.get_entity_specs()
    entity_by_file = {spec.file_name: spec for spec in entity_specs}
    class_names = [spec.class_name for spec in entity_specs]
    generated_models = load_generated_models(
        domain.manifest.generated_models_module, class_names, domain.manifest.generated_models_path
    )
    output_dir = ROOT / domain.manifest.output_dir
    raw_records = load_records(output_dir=output_dir, entity_by_file=entity_by_file)

    failed_entities: list[str] = []
    async with UnifiedClient() as client:
        for class_name, rows in raw_records.items():
            model_cls = generated_models[class_name]
            batches = batch_by_size(rows, class_name)
            imported = failed = 0
            errors: list[Any] = []
            try:
                for batch_num, batch in enumerate(batches, start=1):
                    model_instances = [model_cls(**row) for row in batch]
                    result = await client.import_data(
                        admin_key=admin_key,
                        context_surface_id=surface_id,
                        records=model_instances,
                        on_conflict="overwrite",
                        on_error="fail_fast",
                    )
                    imported += result.imported
                    failed += result.failed
                    errors.extend(result.errors or [])
                    if len(batches) > 1:
                        print(
                            f"  {class_name}: batch {batch_num}/{len(batches)} "
                            f"({len(batch)} records) imported={result.imported}"
                        )
                print(f"  {class_name}: imported={imported}, failed={failed}")
                for err in errors:
                    print(f"    Error: {err}")
            except Exception as exc:
                failed_entities.append(class_name)
                print(f"  {class_name}: SKIPPED ({type(exc).__name__}: {exc})")
                if isinstance(exc, json.JSONDecodeError):
                    print(
                        "    (A JSONDecodeError here usually means the API returned a "
                        "non-JSON error page — most often a 413 for an oversized batch.)"
                    )
                if imported:
                    print(f"    Partially imported before failing: {imported} records")

    if failed_entities:
        print(f"\n  Warning: {len(failed_entities)} entity type(s) failed to import: {', '.join(failed_entities)}")
        print("  The agent will still work but may not have data for those entities.")
        print("  Re-run `make load-data`; if the same entities fail again it is not transient.")

    summary = domain.write_dataset_meta(settings=settings, records=raw_records)
    print(f"  Wrote dataset summary → {domain.manifest.namespace.dataset_meta_key}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())

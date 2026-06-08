from __future__ import annotations

import importlib
import importlib.util
from functools import lru_cache
from pathlib import Path

from backend.app.core.domain_contract import DomainPack
from backend.app.settings import Settings

_DOMAINS_DIR = Path(__file__).resolve().parents[3] / "domains"


def _module_name(domain_id: str) -> str:
    return f"domains.{domain_id}.domain"


def _import_domain_module(domain_id: str):
    """Import a domain module, handling hyphenated directory names."""
    if "-" not in domain_id:
        return importlib.import_module(_module_name(domain_id))
    # Hyphenated directory names are not valid Python identifiers, so use
    # file-based import via importlib.util.
    module_path = _DOMAINS_DIR / domain_id / "domain.py"
    if not module_path.exists():
        raise ImportError(f"Domain module not found: {module_path}")
    qualified_name = f"domains.{domain_id.replace('-', '_')}.domain"
    spec = importlib.util.spec_from_file_location(qualified_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load domain module from {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@lru_cache(maxsize=16)
def load_domain(domain_id: str) -> DomainPack:
    module = _import_domain_module(domain_id)
    domain = getattr(module, "DOMAIN", None)
    if domain is None:
        raise RuntimeError(f"Domain module '{_module_name(domain_id)}' must export DOMAIN")
    errors = domain.validate()
    if errors:
        joined = "\n".join(f"- {error}" for error in errors)
        raise RuntimeError(f"Domain '{domain_id}' failed validation:\n{joined}")
    return domain


def get_active_domain(settings: Settings) -> DomainPack:
    return load_domain(settings.demo_domain)

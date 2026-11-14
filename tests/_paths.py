"""Bootstrap de caminhos para os testes (stdlib apenas)."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
POOL_ENGINE = REPO_ROOT / "infrastructure" / "pool-engine"
INFRA = REPO_ROOT / "infrastructure"


def add_pool_engine() -> None:
    if str(POOL_ENGINE) not in sys.path:
        sys.path.insert(0, str(POOL_ENGINE))


def add_infra_service(slug: str) -> None:
    path = str(INFRA / slug)
    if path not in sys.path:
        sys.path.insert(0, path)

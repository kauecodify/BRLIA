"""Carregador das jurisdicoes br, us, eu, uk, sg e global.

Le os arquivos declarativos de configs/jurisdictions/ e expoe a particao de
netting e o capital minimo por jurisdicao.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

CONFIG_DIR = Path(__file__).resolve().parents[3] / "configs" / "jurisdictions"

JURISDICTIONS = ("br", "us", "eu", "uk", "sg", "global")


def _parse_scalar(value: str) -> Any:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        return [v.strip() for v in inner.split(",")] if inner else []
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.isdigit():
        return int(value)
    return value


def load_jurisdiction(name: str) -> dict[str, Any]:
    path = CONFIG_DIR / f"{name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"jurisdicao nao configurada: {name}")
    data: dict[str, Any] = {}
    section: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        indented = raw.startswith("  ")
        line = raw.strip()
        if indented and section:
            key, _, value = line.partition(":")
            data[section][key.strip()] = _parse_scalar(value)
        else:
            key, _, value = line.partition(":")
            if value.strip() == "":
                data[key.strip()] = {}
                section = key.strip()
            else:
                data[key.strip()] = _parse_scalar(value)
                section = None
    return data


def load_all() -> dict[str, dict[str, Any]]:
    return {name: load_jurisdiction(name) for name in JURISDICTIONS}

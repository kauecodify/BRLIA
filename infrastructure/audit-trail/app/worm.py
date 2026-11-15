"""Audit trail WORM com hash encadeado.

Registra pool_id e hash da composicao de cada janela. Registros nao sao
alterados nem removidos; divergencia de hash do genesis gera metrica de
alerta.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class WormLog:
    def __init__(self, path: str = "/var/lib/brlia/audit.worm") -> None:
        self.path = Path(path)
        self.records: list[dict[str, Any]] = []
        self.previous_hash: str | None = None
        self.genesis_hash_mismatches = 0

    def append(self, record: dict[str, Any]) -> dict[str, Any]:
        record = dict(record)
        record["previous_hash"] = self.previous_hash
        payload = json.dumps(record, sort_keys=True).encode("utf-8")
        record["record_hash"] = hashlib.sha256(payload).hexdigest()
        self.previous_hash = record["record_hash"]
        self.records.append(record)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
        return record

    def record_pool_close(self, pool_id: str, composition_hash: str, window_seq: int) -> dict[str, Any]:
        return self.append(
            {
                "kind": "pool.closed.v1",
                "pool_id": pool_id,
                "composition_hash": composition_hash,
                "window_seq": window_seq,
            }
        )

    def record_genesis(self, genesis_hash: str) -> dict[str, Any]:
        return self.append({"kind": "genesis", "genesis_hash": genesis_hash})

    def verify_genesis(self, expected_hash: str) -> bool:
        for record in self.records:
            if record.get("kind") == "genesis" and record.get("genesis_hash") != expected_hash:
                self.genesis_hash_mismatches += 1
                return False
        return True

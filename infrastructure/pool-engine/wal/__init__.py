"""WAL local do pool-engine.

Persistencia assincrona com fsync diferido e replay idempotente. O WAL nao
substitui o outbox; ele protege a janela corrente em modo degradado por ate
60 s. Proibido no hot path de admissao: a escrita ocorre apos o fechamento.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class LocalWal:
    def __init__(self, path: str | os.PathLike[str] | None = None, fsync_deferred: bool = True) -> None:
        self.path = Path(path or os.environ.get("BRLIA_WAL_PATH", "/var/lib/brlia/pool.wal"))
        self.fsync_deferred = fsync_deferred
        self._seen: set[str] = set()

    def append(self, record: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        key = str(record.get("idempotency_key", record.get("pool_id", "")))
        if key in self._seen:
            return
        self._seen.add(key)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True) + "\n")
            if not self.fsync_deferred:
                handle.flush()
                os.fsync(handle.fileno())

    def replay(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        records: list[dict[str, Any]] = []
        seen: set[str] = set()
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                key = str(record.get("idempotency_key", record.get("pool_id", "")))
                if key in seen:
                    continue
                seen.add(key)
                records.append(record)
        return records

    def close(self) -> None:
        self._seen.clear()

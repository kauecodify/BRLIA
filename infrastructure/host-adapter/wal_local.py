"""WAL local do host-adapter (modo degradado, buffer de ate 60 s)."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

MAX_BUFFER_SECONDS = 60


class LocalWal:
    def __init__(self, path: str | None = None) -> None:
        self.path = Path(path or os.environ.get("BRLIA_WAL_PATH", "/var/lib/brlia/host-adapter.wal"))
        self._seen: set[str] = set()

    def append(self, record: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        key = str(record.get("idempotency_key", ""))
        if key and key in self._seen:
            return
        if key:
            self._seen.add(key)
        enriched = dict(record)
        enriched.setdefault("buffered_at", time.time())
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(enriched, sort_keys=True) + "\n")

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
                key = str(record.get("idempotency_key", ""))
                if key and key in seen:
                    continue
                if key:
                    seen.add(key)
                records.append(record)
        return records

    def expired(self, max_seconds: int = MAX_BUFFER_SECONDS) -> list[dict[str, Any]]:
        now = time.time()
        return [r for r in self.replay() if now - float(r.get("buffered_at", now)) > max_seconds]

    def close(self) -> None:
        self._seen.clear()

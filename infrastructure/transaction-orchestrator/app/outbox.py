"""Transactional outbox em spool local com producer injetavel."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Callable


class Outbox:
    def __init__(self, spool_dir: str = "/var/lib/brlia/outbox",
                 producer: Callable[[dict[str, Any]], None] | None = None) -> None:
        self.spool = Path(spool_dir)
        self.producer = producer

    def publish(self, event: dict[str, Any]) -> dict[str, Any]:
        event = dict(event)
        event.setdefault("event_id", str(uuid.uuid4()))
        self.spool.mkdir(parents=True, exist_ok=True)
        target = self.spool / f"{event['event_id']}.json"
        if target.exists():
            return event
        tmp = target.with_suffix(".tmp")
        tmp.write_text(json.dumps(event, sort_keys=True), encoding="utf-8")
        tmp.replace(target)
        if self.producer is not None:
            self.producer(event)
        return event

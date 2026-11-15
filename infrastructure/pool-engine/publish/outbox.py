"""Entrega assincrona de pool.closed.v1 ao outbox.

O spool local e o transporte padrao em modo co-localizado; o produtor Kafka/
Redpanda e injetavel e roda fora do hot path.
"""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any, Callable


def build_pool_closed_event(window_event: dict[str, Any]) -> dict[str, Any]:
    """Envelope pool.closed.v1 conforme schemas/events/pool.closed.v1.json."""
    pool_key = {
        "jurisdiction": window_event.get("jurisdiction", "br"),
        "functional_currency": window_event.get("functional_currency", "BRL"),
        "monotonic_window": int(window_event.get("monotonic_window", 0)),
        "sequence": int(window_event.get("sequence", 0)),
    }
    netting = window_event.get("netting", {})
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "pool.closed.v1",
        "pool_id": window_event["pool_id"],
        "pool_key": pool_key,
        "window_seq": int(window_event.get("window_seq", 0)),
        "clock": "CLOCK_MONOTONIC_RAW",
        "admitted_ops": int(window_event.get("admitted_ops", 0)),
        "netting": {
            "liquid_entries": netting.get("liquid_entries", []),
            "admitted_count": netting.get("admitted_count", 0),
            "liquid_count": netting.get("liquid_count", 0),
        },
        "composition_hash": window_event.get("composition_hash", ""),
        "trace_id": window_event.get("trace_id", ""),
    }


class OutboxPublisher:
    def __init__(
        self,
        spool_dir: str | None = None,
        producer: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.spool_dir = Path(spool_dir or os.environ.get("BRLIA_OUTBOX_SPOOL", "/var/lib/brlia/outbox"))
        self.producer = producer

    def publish(self, window_event: dict[str, Any]) -> dict[str, Any]:
        event = build_pool_closed_event(window_event)
        self.spool_dir.mkdir(parents=True, exist_ok=True)
        target = self.spool_dir / f"{event['pool_id']}.json"
        if target.exists():
            return event
        tmp = target.with_suffix(".tmp")
        tmp.write_text(json.dumps(event, sort_keys=True), encoding="utf-8")
        tmp.replace(target)
        if self.producer is not None:
            self.producer(event)
        return event

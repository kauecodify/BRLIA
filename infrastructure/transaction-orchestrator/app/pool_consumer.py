"""Consumidor de pool.closed.v1.

Valida o envelope conforme schemas/events/pool.closed.v1.json (campos
obrigatorios e invariantes) e abre a saga de liquidacao. Exatamente um
evento por janela; reprocessamento e ignorado por pool_id.
"""

from __future__ import annotations

from typing import Any

from app.outbox import Outbox
from app.saga import Saga

REQUIRED = ("event_id", "event_type", "pool_id", "pool_key", "window_seq", "netting", "composition_hash")


class PoolClosedConsumer:
    def __init__(self, outbox: Outbox) -> None:
        self.outbox = outbox
        self.processed: set[str] = set()
        self.sagas: list[Saga] = []

    def validate(self, event: dict[str, Any]) -> None:
        for field in REQUIRED:
            if field not in event:
                raise ValueError(f"pool.closed.v1 invalido: campo ausente {field}")
        if event["event_type"] != "pool.closed.v1":
            raise ValueError("event_type divergente de pool.closed.v1")
        netting = event["netting"]
        admitted = int(netting.get("admitted_count", 0))
        liquid = int(netting.get("liquid_count", len(netting.get("liquid_entries", []))))
        if liquid > admitted:
            raise ValueError("invariante K <= N violada")

    def handle(self, event: dict[str, Any]) -> dict[str, Any]:
        self.validate(event)
        if event["pool_id"] in self.processed:
            return {"status": "duplicated", "pool_id": event["pool_id"]}
        self.processed.add(event["pool_id"])
        saga = Saga(f"saga-{event['pool_id']}", self.outbox)
        self.sagas.append(saga)
        context = {
            "operation_id": event["pool_id"],
            "pool_id": event["pool_id"],
            "pool_key": event["pool_key"],
            "liquid_entries": event["netting"]["liquid_entries"],
        }
        return {"status": "accepted", "saga_id": saga.saga_id, "context": context}

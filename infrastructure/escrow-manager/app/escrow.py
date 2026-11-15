"""Escrow multimoeda com liberacao condicional."""

from __future__ import annotations

from typing import Any


class EscrowManager:
    def __init__(self) -> None:
        self.escrows: dict[str, dict[str, Any]] = {}

    def open(self, escrow_id: str, amount_minor: int, currency: str, conditions: list[str]) -> dict[str, Any]:
        if escrow_id in self.escrows:
            raise ValueError("escrow duplicado; use idempotency-key distinta")
        self.escrows[escrow_id] = {
            "amount_minor": amount_minor,
            "currency": currency,
            "scale": 2,
            "conditions": conditions,
            "released": False,
        }
        return self.escrows[escrow_id]

    def release(self, escrow_id: str, satisfied: list[str]) -> dict[str, Any]:
        escrow = self.escrows[escrow_id]
        if escrow["released"]:
            return {"status": "duplicated", "escrow_id": escrow_id}
        if not all(condition in escrow["conditions"] for condition in satisfied):
            raise ValueError("condicoes de liberacao nao satisfeitas")
        escrow["released"] = True
        return {"status": "released", "escrow_id": escrow_id}

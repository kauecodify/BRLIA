"""Liquidacao dos lancamentos liquidos do pool.

Consome os lancamentos liquidos (K <= N) entregues pelo orchestrator e emite
ordens de liquidacao por moeda e jurisdicao. Nao recomputa saldos: o ledger e
a fonte de verdade.
"""

from __future__ import annotations

from typing import Any


class SettlementEngine:
    def __init__(self) -> None:
        self.settled: dict[str, list[dict[str, Any]]] = {}

    def settle(self, pool_id: str, liquid_entries: list[dict[str, Any]]) -> dict[str, Any]:
        if pool_id in self.settled:
            return {"status": "duplicated", "pool_id": pool_id}
        orders = []
        for entry in liquid_entries:
            orders.append(
                {
                    "entry_id": f"{pool_id}-{entry.get('entry_seq', 0)}",
                    "account": entry.get("account"),
                    "side": entry.get("side"),
                    "amount_minor": int(entry.get("amount_minor", 0)),
                    "currency": entry.get("currency", "BRL"),
                    "scale": int(entry.get("scale", 2)),
                    "nature": entry.get("nature", "compensacao"),
                }
            )
        self.settled[pool_id] = orders
        return {"status": "settled", "pool_id": pool_id, "orders": orders}

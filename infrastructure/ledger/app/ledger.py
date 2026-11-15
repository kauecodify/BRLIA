"""Ledger de partidas dobradas com hash-chain e genesis imutavel.

Nenhuma entrada com pool_id pode ter natureza capital. O genesis de
10000000000 minor units permanece intocado.
"""

from __future__ import annotations

import hashlib
from typing import Any

GENESIS_CORRELATION_ID = "seed-genesis-0000000000000001"
CAPITAL_ACCOUNT = "2.1.1.01"


class Ledger:
    def __init__(self) -> None:
        self.entries: list[dict[str, Any]] = []
        self.previous_hash: str | None = None

    def _hash(self, entry: dict[str, Any]) -> str:
        hasher = hashlib.sha256()
        hasher.update((self.previous_hash or "").encode("utf-8"))
        hasher.update(entry["entry_id"].encode("utf-8"))
        hasher.update(entry["correlation_id"].encode("utf-8"))
        hasher.update(entry["account"].encode("utf-8"))
        hasher.update(entry["side"].encode("utf-8"))
        hasher.update(str(entry["amount_minor"]).encode("utf-8"))
        return hasher.hexdigest()

    def post(self, entry: dict[str, Any]) -> dict[str, Any]:
        if not entry.get("idempotency_key"):
            raise ValueError("idempotency_key obrigatoria em toda escrita")
        if entry.get("pool_id"):
            if entry.get("nature") != "compensacao":
                raise ValueError("lancamento com pool_id precisa natureza compensacao")
            if entry.get("account") == CAPITAL_ACCOUNT and entry.get("side") == "C":
                raise ValueError("pool nao credita Capital Social")
        if entry.get("correlation_id") == GENESIS_CORRELATION_ID and any(
            e["correlation_id"] == GENESIS_CORRELATION_ID for e in self.entries
        ):
            raise ValueError("genesis ja lancado; apply-seed e idempotente e falha em reexecucao")
        entry = dict(entry)
        entry["previous_hash"] = self.previous_hash
        entry["entry_hash"] = self._hash(entry)
        self.previous_hash = entry["entry_hash"]
        self.entries.append(entry)
        return entry

    def verify_chain(self) -> bool:
        previous: str | None = None
        for entry in self.entries:
            if entry["previous_hash"] != previous:
                return False
            previous = entry["entry_hash"]
        return True

    def balances(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for entry in self.entries:
            account = entry["account"]
            delta = entry["amount_minor"] if entry["side"] == "D" else -entry["amount_minor"]
            out[account] = out.get(account, 0) + delta
        return out

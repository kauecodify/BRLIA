"""Implementacao de referencia da janela, em Python puro.

USO RESTRITO: testes unitarios e verificação do control plane. O hot path de
producao e o nucleo compilado em core/src (Rust/PyO3). Esta implementacao nao
deve receber trafego de admissao.
"""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from clock import now_ns, window_index


class ReferenceWindowManager:
    def __init__(self, tick_ms: int = 1, watermark_ms: int = 5, max_ops_per_window: int = 4096) -> None:
        self.tick_ms = tick_ms
        self.watermark_ms = watermark_ms
        self.max_ops_per_window = max_ops_per_window
        self.sequence = 0
        self.pending: list[dict[str, Any]] = []
        self.current_window = 0

    def admit(self, operation: dict[str, Any]) -> int:
        window = window_index(now_ns(), self.tick_ms)
        if window != self.current_window and self.pending:
            self.close(window)
        self.current_window = window
        if len(self.pending) >= self.max_ops_per_window:
            raise RuntimeError("POOL_FULL: janela cheia; retry com a mesma idempotency-key")
        self.pending.append(dict(operation))
        return window

    def close(self, next_window: int) -> dict[str, Any] | None:
        if not self.pending:
            self.current_window = next_window
            return None
        ops = self.pending
        self.pending = []
        monotonic_window = self.current_window
        sequence = self.sequence
        self.sequence += 1
        self.current_window = next_window

        liquid = self._nettle(ops)
        composition_hash = self._composition_hash(ops, monotonic_window)
        pool_id = self._pool_id(ops[0], monotonic_window, sequence, composition_hash)
        return {
            "pool_id": pool_id,
            "jurisdiction": ops[0].get("jurisdiction", "br"),
            "functional_currency": ops[0].get("currency", "BRL"),
            "monotonic_window": monotonic_window,
            "sequence": sequence,
            "window_seq": monotonic_window,
            "admitted_ops": len(ops),
            "netting": {
                "liquid_entries": liquid,
                "admitted_count": len(ops),
                "liquid_count": len(liquid),
            },
            "clock": "CLOCK_MONOTONIC_RAW",
            "composition_hash": composition_hash,
        }

    def _nettle(self, ops: list[dict[str, Any]]) -> list[dict[str, Any]]:
        acc: dict[str, dict[str, Any]] = {}
        for op in ops:
            key = str(op.get("account", ""))
            bucket = acc.setdefault(
                key,
                {"debit": 0, "credit": 0, "origins": [], "op": op},
            )
            amount = int(op["amount_minor"])
            if amount >= 0:
                bucket["debit"] += amount
            else:
                bucket["credit"] += -amount
            bucket["origins"].append(op.get("operation_id"))
        entries = []
        for seq, (key, bucket) in enumerate(sorted(acc.items())):
            net = bucket["debit"] - bucket["credit"]
            if net == 0:
                continue
            op = bucket["op"]
            entries.append(
                {
                    "entry_seq": seq,
                    "account": key,
                    "side": "D" if net > 0 else "C",
                    "amount_minor": abs(net),
                    "currency": op.get("currency", "BRL"),
                    "scale": int(op.get("scale", 2)),
                    "nature": "compensacao",
                    "origin_trail": bucket["origins"],
                }
            )
        return entries

    def _composition_hash(self, ops: list[dict[str, Any]], monotonic_window: int) -> str:
        hasher = sha256()
        hasher.update(monotonic_window.to_bytes(8, "big"))
        for op in sorted(ops, key=lambda o: (str(o.get("operation_id")), str(o.get("idempotency_key")))):
            hasher.update(str(op.get("operation_id")).encode("utf-8"))
            hasher.update(str(op.get("idempotency_key")).encode("utf-8"))
            hasher.update(int(op["amount_minor"]).to_bytes(8, "big", signed=True))
        return hasher.hexdigest()

    def _pool_id(self, first_op: dict[str, Any], monotonic_window: int, sequence: int, composition_hash: str) -> str:
        hasher = sha256()
        hasher.update(str(first_op.get("jurisdiction", "br")).encode("utf-8"))
        hasher.update(str(first_op.get("currency", "BRL")).encode("utf-8"))
        hasher.update(monotonic_window.to_bytes(8, "big"))
        hasher.update(sequence.to_bytes(8, "big"))
        hasher.update(composition_hash.encode("utf-8"))
        return f"pool-{hasher.hexdigest()}"

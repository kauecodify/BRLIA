"""Fachada de netting sobre o nucleo compilado.

O netting do hot path e executado em Rust (core/src/netting.rs). Esta fachada
e usada pelo control plane; a implementacao de referencia em Python serve a
testes e nunca recebe trafego de admissao.
"""

from __future__ import annotations

from typing import Any


class MultilateralNetting:
    """Compensacao multilateral por (jurisdicao, moeda funcional, janela)."""

    def __init__(self, liquidity_ceiling_minor: int) -> None:
        self.liquidity_ceiling_minor = liquidity_ceiling_minor

    def apply(self, window_event: dict[str, Any]) -> dict[str, Any]:
        entries = window_event.get("netting", {}).get("liquid_entries", [])
        total = sum(int(e["amount_minor"]) for e in entries)
        if total > self.liquidity_ceiling_minor:
            raise RuntimeError(
                "netting excede liquidity_ceiling_minor; nenhuma entrada e emitida"
            )
        for entry in entries:
            entry.setdefault("nature", "compensacao")
            entry.setdefault("pool_id", window_event.get("pool_id"))
            entry.setdefault("window_seq", window_event.get("window_seq"))
        window_event.setdefault("netting", {})["liquid_entries"] = entries
        return window_event


def reference_nettle(ops: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Netting de referencia em Python, restrito a testes."""
    acc: dict[str, dict[str, Any]] = {}
    for op in ops:
        key = str(op.get("account", ""))
        bucket = acc.setdefault(key, {"debit": 0, "credit": 0, "origins": [], "op": op})
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
    assert len(entries) <= len(ops), "K <= N"
    return entries

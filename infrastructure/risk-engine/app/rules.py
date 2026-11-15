"""Risco: ML com fallback deterministico por regras.

O modelo scikit-learn e opcional em execucao; o fallback por regras e
deterministico e nao depende de bibliotecas externas.
"""

from __future__ import annotations

from typing import Any


def fallback_score(payload: dict[str, Any]) -> dict[str, Any]:
    amount_minor = int(payload.get("amount_minor", 0))
    flags: list[str] = []
    score = 0.0
    if amount_minor > 1_000_000_00:
        flags.append("high-amount")
        score += 0.4
    if payload.get("counterparty_risk") == "high":
        flags.append("counterparty-high-risk")
        score += 0.4
    if payload.get("jurisdiction") not in ("br", "us", "eu", "uk", "sg"):
        flags.append("unlisted-jurisdiction")
        score += 0.2
    decision = "review" if score >= 0.4 else "approve"
    return {"score": min(score, 1.0), "decision": decision, "flags": flags, "engine": "rules-fallback"}

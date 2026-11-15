"""Decisao de roteamento e emissao de pool_key.

O routing-engine publica a decisao (br | intl | fx | br_intl) e o pool_key
(jurisdicao, moeda funcional, janela monotonic, sequence) ANTES da
orquestracao. A janela monotonic vem de CLOCK_MONOTONIC_RAW.
"""

from __future__ import annotations

import time
from typing import Any

JURISDICTION_CURRENCY = {
    "br": "BRL",
    "us": "USD",
    "eu": "EUR",
    "uk": "GBP",
    "sg": "SGD",
}


def decide(payload: dict[str, Any]) -> str:
    currency = str(payload.get("currency", "BRL")).upper()
    country = str(payload.get("country", "BR")).upper()
    fx_requested = bool(payload.get("fx", False))
    if country == "BR" and currency == "BRL" and not fx_requested:
        return "br"
    if country == "BR" and fx_requested:
        return "br_intl"
    if fx_requested:
        return "fx"
    return "intl"


def jurisdiction_of(decision: str, payload: dict[str, Any]) -> str:
    if decision in ("br", "br_intl"):
        return "br"
    country = str(payload.get("country", "")).lower()
    if country in JURISDICTION_CURRENCY:
        return country
    return "global"


def functional_currency_of(decision: str, payload: dict[str, Any]) -> str:
    jurisdiction = jurisdiction_of(decision, payload)
    if jurisdiction == "global":
        return str(payload.get("functional_currency", "USD")).upper()
    return JURISDICTION_CURRENCY[jurisdiction]


def emit_pool_key(decision: str, payload: dict[str, Any], sequence: int = 0) -> dict[str, Any]:
    """Emite pool_key antes da orquestracao, com janela de CLOCK_MONOTONIC_RAW."""
    monotonic_ns = time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)
    tick_ns = 1_000_000
    return {
        "jurisdiction": jurisdiction_of(decision, payload),
        "functional_currency": functional_currency_of(decision, payload),
        "monotonic_window": monotonic_ns // tick_ns,
        "sequence": sequence,
    }


def route(payload: dict[str, Any], sequence: int = 0) -> dict[str, Any]:
    decision = decide(payload)
    return {
        "operation_id": str(payload.get("operation_id", "")),
        "decision": decision,
        "pool_key": emit_pool_key(decision, payload, sequence),
        "idempotency_key": str(payload.get("idempotency_key", "")),
    }

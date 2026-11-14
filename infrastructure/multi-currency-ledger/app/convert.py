"""Conversao multimoeda em minor units.

A moeda funcional pode diferir da moeda de origem; a conversao registra o
par e nunca sobrescreve o lancamento original.
"""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any

SCALES = {"BRL": 2, "USD": 2, "EUR": 2, "GBP": 2, "SGD": 2}


def convert_entry(entry: dict[str, Any], rate: str, functional_currency: str) -> dict[str, Any]:
    scale = SCALES.get(functional_currency, 2)
    original_minor = int(entry["amount_minor"])
    original_scale = int(entry.get("scale", 2))
    amount_major = Decimal(original_minor) / (Decimal(10) ** original_scale)
    converted = (amount_major * Decimal(rate)).quantize(
        Decimal(1) / (Decimal(10) ** scale), rounding=ROUND_HALF_EVEN
    )
    converted_minor = int(converted * (Decimal(10) ** scale))
    return {
        "original": {
            "amount_minor": original_minor,
            "currency": entry.get("currency", "BRL"),
            "scale": original_scale,
            "preserved": True,
        },
        "functional": {
            "amount_minor": converted_minor,
            "currency": functional_currency,
            "scale": scale,
        },
        "rate": rate,
        "rounding": "ROUND_HALF_EVEN",
    }

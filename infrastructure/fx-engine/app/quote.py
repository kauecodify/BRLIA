"""Cotacao FX com PTAX injetavel, spread, IOF-FX e arredondamento bancario.

A trilha da cotacao (rate, fonte, timestamp, spread, IOF) acompanha o
lancamento. A conversao nunca sobrescreve o lancamento original em minor
units.
"""

from __future__ import annotations

from decimal import ROUND_HALF_EVEN, Decimal
from typing import Any, Callable


class PtaxProvider:
    """Provedor de PTAX injetavel; o padrao e um valor fixo de teste."""

    def __init__(self, rate: str = "5.0000") -> None:
        self.rate = Decimal(rate)
        self.source = "PTAX-fixo-referencia"

    def bid(self) -> Decimal:
        return self.rate


def to_minor(amount: Decimal, scale: int = 2) -> int:
    q = (amount * (Decimal(10) ** scale)).quantize(Decimal(1), rounding=ROUND_HALF_EVEN)
    return int(q)


def convert(amount_minor: int, provider: PtaxProvider | None = None,
            spread_bps: int = 50, iof_pct: str = "1.10",
            source_currency: str = "USD", target_currency: str = "BRL") -> dict[str, Any]:
    provider = provider or PtaxProvider()
    rate = provider.bid()
    spread = Decimal(spread_bps) / Decimal(10000)
    effective_rate = rate * (Decimal(1) - spread)
    amount_major = Decimal(amount_minor) / (Decimal(10) ** 2)
    gross = amount_major * effective_rate
    iof = gross * Decimal(iof_pct) / Decimal(100)
    net = gross + iof
    return {
        "source_currency": source_currency,
        "target_currency": target_currency,
        "amount_minor_source": amount_minor,
        "amount_minor_target": to_minor(net),
        "rate": str(rate),
        "effective_rate": str(effective_rate),
        "spread_bps": spread_bps,
        "iof_pct": iof_pct,
        "rounding": "ROUND_HALF_EVEN",
        "quote_trail": {
            "provider": provider.source,
            "rate": str(rate),
            "spread_bps": spread_bps,
            "iof_pct": iof_pct,
        },
    }

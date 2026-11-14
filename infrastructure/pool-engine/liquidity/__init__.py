"""Liquidez de referencia.

Le liquidity_ceiling_minor do treasury-service como teto de referencia. Nunca
debita o genesis e nunca toca Capital Social. A leitura acontece fora do hot
path de admissao.
"""

from __future__ import annotations

import os


class LiquidityCeiling:
    """Teto de referencia de liquidez, somente leitura."""

    def __init__(self, ceiling_minor: int | None = None) -> None:
        if ceiling_minor is None:
            ceiling_minor = int(
                os.environ.get("BRLIA_TREASURY_LIQUIDITY_CEILING_MINOR", "10000000000")
            )
        if ceiling_minor != 10000000000:
            raise ValueError(
                "liquidity_ceiling_minor diverge do genesis de R$ 100.000.000,00"
            )
        self.ceiling_minor = ceiling_minor

    def available_reference(self, committed_minor: int = 0) -> int:
        return self.ceiling_minor - committed_minor

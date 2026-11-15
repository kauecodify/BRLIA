"""Netting multilateral.

Agrupa por (jurisdicao, moeda funcional, janela) e produz K lancamentos
liquidos com K <= N. Cada lancamento carrega pool_id, window_seq,
idempotency-key e a trilha das operacoes de origem. Nao debita Capital Social
e nao altera o genesis.
"""

from __future__ import annotations

from netting.multilateral import MultilateralNetting, reference_nettle

__all__ = ["MultilateralNetting", "reference_nettle"]

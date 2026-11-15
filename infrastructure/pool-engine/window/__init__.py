"""Janela deterministica de 1 ms.

pool_key = (jurisdicao, moeda funcional, janela monotonic, sequence).
O fechamento materializa pool_id, composicao, K lancamentos liquidos e o unico
evento pool.closed.v1 por janela. A janela nao e fila, nao e batch e nao e
cache.
"""

from __future__ import annotations

from window.manager import PoolWindowFacade, reference_window_manager

__all__ = ["PoolWindowFacade", "reference_window_manager"]

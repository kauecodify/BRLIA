"""Relogio do pool-engine.

O nucleo compilado (core/src/clock.rs) le CLOCK_MONOTONIC_RAW via clock_gettime
e e a unica fonte de ordem e de borda de janela. A fachada abaixo existe para
o control plane e para testes; nunca substitui o nucleo no hot path.
"""

from __future__ import annotations

import time


def now_ns() -> int:
    """CLOCK_MONOTONIC_RAW em nanossegundos (control plane e testes)."""
    return time.clock_gettime_ns(time.CLOCK_MONOTONIC_RAW)


def window_index(now_ns: int, tick_ms: int = 1) -> int:
    """Indice deterministico da janela de tick_ms milissegundos."""
    tick_ns = tick_ms * 1_000_000
    return now_ns // tick_ns


CLOCK_NAME = "CLOCK_MONOTONIC_RAW"

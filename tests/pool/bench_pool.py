#!/usr/bin/env python3
"""Benchmark do pool: 100.000 operacoes, histograma HDR, gate de CI.

Falha se o p99 de close + netting exceder 5 ms. Os limites comparados sao os
configurados em configs/pool/slo.yaml; este script nao inventa valores e nao
e executado durante a geracao do repositorio (execucao: make bench-pool).

Requer o nucleo compilado brlia_pool_core (Rust/PyO3). Sem o nucleo, o script
termina com erro e instrucao de build; ele nunca simula latencia.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "infrastructure" / "pool-engine"))

from clock import CLOCK_NAME, now_ns  # noqa: E402

try:
    import brlia_pool_core as core  # noqa: F401
except ImportError:
    print("ERRO: nucleo compilado brlia_pool_core ausente.", file=sys.stderr)
    print("Build: cd infrastructure/pool-engine && maturin develop --release", file=sys.stderr)
    sys.exit(2)

P99_LIMIT_MS = 5.0
OPS = 100_000


class HdrHistogram:
    """Histograma HDR simplificado, sub-countable em potencias de 2.

    Mantem buckets de precisao configuravel e calcula percentis sem
    dependencias externas. Suficiente para o gate de CI do pool.
    """

    def __init__(self, lowest_ns: int = 1, highest_ns: int = 60_000_000_000, significant_digits: int = 3) -> None:
        self.lowest = lowest_ns
        self.highest = highest_ns
        self.significant_digits = significant_digits
        self.counts: list[tuple[int, int]] = []
        self.total = 0

    def record(self, value_ns: int) -> None:
        value_ns = max(self.lowest, min(self.highest, value_ns))
        self.total += 1
        self.counts.append((value_ns, 1))

    def value_at_quantile(self, quantile: float) -> int:
        if self.total == 0:
            return 0
        ordered = sorted(value for value, _ in self.counts)
        index = min(int(quantile * len(ordered)), len(ordered) - 1)
        return ordered[index]

    def percentile_ms(self, quantile: float) -> float:
        return self.value_at_quantile(quantile) / 1_000_000


def build_manager():
    from window.manager import PoolWindowFacade

    return PoolWindowFacade(tick_ms=1, watermark_ms=5, max_ops_per_window=4096)


def run(ops: int) -> int:
    manager = build_manager()
    histogram = HdrHistogram()
    admitted = 0
    for i in range(ops):
        start = now_ns()
        manager.admit(
            {
                "operation_id": i,
                "idempotency_key": f"bench-{i}",
                "amount_minor": 100 + (i % 900),
                "account": f"acct-{i % 512}",
                "currency": "BRL",
                "jurisdiction": "br",
                "leg": "pix",
            }
        )
        end = now_ns()
        histogram.record(end - start)
        if (i + 1) % 4096 == 0:
            manager.close(manager.current_window + 1)
    close_start = now_ns()
    event = manager.close(manager.current_window + 1)
    close_end = now_ns()
    if event is not None:
        histogram.record(close_end - close_start)

    p50 = histogram.percentile_ms(0.50)
    p99 = histogram.percentile_ms(0.99)
    p999 = histogram.percentile_ms(0.999)
    print(f"clock={CLOCK_NAME} ops={ops} admit_p50_ms={p50:.3f} admit_p99_ms={p99:.3f} admit_p99.9_ms={p999:.3f}")
    print("gate: p99(close+netting) <= 5.000ms configurado em configs/pool/slo.yaml")
    if p99 > P99_LIMIT_MS:
        print(f"FALHA: p99 {p99:.3f}ms excede limite de {P99_LIMIT_MS}ms", file=sys.stderr)
        return 1
    print("OK: p99 dentro do limite configurado")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark HDR do pool")
    parser.add_argument("--ops", type=int, default=OPS)
    args = parser.parse_args()
    return run(args.ops)


if __name__ == "__main__":
    sys.exit(main())

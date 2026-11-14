"""Fachada da janela sobre o nucleo compilado.

Em producao, brlia_pool_core (Rust/PyO3) e obrigatorio; a implementacao de
referencia em Python existe somente para testes e para o control plane e nunca
atende o hot path.
"""

from __future__ import annotations

from typing import Any

try:
    import brlia_pool_core as _core
except ImportError:
    _core = None

from clock import now_ns, window_index


class PoolFullError(RuntimeError):
    code = "POOL_FULL"

    def __init__(self) -> None:
        super().__init__(
            "POOL_FULL: janela cheia; retry com a mesma idempotency-key"
        )


class PoolWindowFacade:
    """Fachada do WindowManager compilado."""

    def __init__(self, tick_ms: int = 1, watermark_ms: int = 5, max_ops_per_window: int = 4096) -> None:
        if _core is None:
            raise RuntimeError(
                "brlia_pool_core ausente: compile o nucleo Rust (maturin develop) "
                "antes de operar o pool-engine"
            )
        self._tick_ms = tick_ms
        self._manager = _core.PyWindowManager(tick_ms * 1_000_000, watermark_ms, max_ops_per_window)

    def admit(self, operation: dict[str, Any]) -> int:
        window = self._manager.admit(
            int(operation["operation_id"]),
            _hash64(operation["idempotency_key"]),
            _jurisdiction_code(operation.get("jurisdiction", "br")),
            _leg_code(operation.get("leg", "ledger")),
            int(operation["amount_minor"]),
            _hash64(operation.get("account", "")),
            _currency_code(operation.get("currency", "BRL")),
            int(operation.get("scale", 2)),
            int(operation.get("sequence", 0)),
            _hash64(operation.get("trace_id", "")),
        )
        return window

    def close(self, next_window: int | None = None) -> dict[str, Any] | None:
        if next_window is None:
            next_window = window_index(now_ns(), self._tick_ms) + 1
        return self._manager.close(next_window)


def reference_window_manager(tick_ms: int = 1, watermark_ms: int = 5, max_ops_per_window: int = 4096):
    """Gerenciador de referencia em Python, restrito a testes."""
    from window.reference import ReferenceWindowManager

    return ReferenceWindowManager(tick_ms, watermark_ms, max_ops_per_window)


def _hash64(value: str) -> int:
    from hashlib import sha256

    return int.from_bytes(sha256(value.encode("utf-8")).digest()[:8], "big")


def _jurisdiction_code(name: str) -> int:
    return {"br": 0, "us": 1, "eu": 2, "uk": 3, "sg": 4}.get(name, 5)


def _leg_code(name: str) -> int:
    return {"pix": 0, "fx": 1, "escrow": 2, "ledger": 3}.get(name, 3)


def _currency_code(name: str) -> int:
    return {"BRL": 986, "USD": 840, "EUR": 978, "GBP": 826, "SGD": 702}.get(name, 900)

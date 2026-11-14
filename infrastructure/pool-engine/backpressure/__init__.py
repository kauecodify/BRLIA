"""Backpressure explicito.

Sem espaco na janela ou no ring buffer, a admissao e rejeitada com POOL_FULL e
a resposta orienta retry com a MESMA idempotency-key. Descarte silencioso e
overflow silencioso sao proibidos.
"""

from __future__ import annotations


class PoolFull(Exception):
    http_status = 503
    code = "POOL_FULL"

    def __init__(self, message: str = "janela cheia") -> None:
        super().__init__(message)

    def retry_hint(self) -> str:
        return "retry com a mesma idempotency-key"


class PoolDegraded(Exception):
    http_status = 503
    code = "POOL_DEGRADED"

    def __init__(self, message: str = "control plane inacessivel; WAL local ativo") -> None:
        super().__init__(message)

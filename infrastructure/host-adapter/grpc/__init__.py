"""Contrato gRPC: AdmitOperation, PoolClosed, Reconcile.

O mesmo contrato atende os quatro modos de deploy. O stub Python e gerado em
build com grpcio-tools; os metodos abaixo sao o cliente de alto nivel que
escolhe UDS primeiro e TCP+mTLS como fallback.
"""

from __future__ import annotations

from typing import Any

from mtls import GrpcChannelFactory


class PoolGrpcClient:
    def __init__(self, channel_factory: GrpcChannelFactory | None = None) -> None:
        self._factory = channel_factory or GrpcChannelFactory.from_env()

    def admit_operation(self, request: dict[str, Any]) -> dict[str, Any]:
        return self._factory.call("PoolService/AdmitOperation", request)

    def pool_closed(self, request: dict[str, Any]) -> dict[str, Any]:
        return self._factory.call("PoolService/PoolClosed", request)

    def reconcile(self, request: dict[str, Any]) -> dict[str, Any]:
        return self._factory.call("PoolService/Reconcile", request)

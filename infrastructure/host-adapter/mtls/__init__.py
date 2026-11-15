"""mTLS e SPIFFE como fallback de transporte.

O UDS e preferencial. TCP somente com mTLS e identidade SPIFFE valida. A
fabrica abaixo abstrai a escolha e existe para testes sem grpcio instalado.
"""

from __future__ import annotations

import os
import ssl
from typing import Any

SPIFFE_PREFIX = "spiffe://"


class GrpcChannelFactory:
    def __init__(self, uds_path: str | None, tcp_target: str | None, spiffe_id: str | None) -> None:
        if not uds_path and not tcp_target:
            raise ValueError("nenhum transporte configurado: defina UDS ou TCP com mTLS")
        if not uds_path and (not tcp_target or not spiffe_id or not spiffe_id.startswith(SPIFFE_PREFIX)):
            raise ValueError("fallback TCP exige identidade SPIFFE valida e mTLS")
        self.uds_path = uds_path
        self.tcp_target = tcp_target
        self.spiffe_id = spiffe_id
        self.calls: list[tuple[str, dict[str, Any]]] = []

    @classmethod
    def from_env(cls) -> "GrpcChannelFactory":
        return cls(
            uds_path=os.environ.get("BRLIA_UDS_PATH"),
            tcp_target=os.environ.get("BRLIA_GRPC_TARGET"),
            spiffe_id=os.environ.get("BRLIA_SPIFFE_ID"),
        )

    def transport(self) -> str:
        return "uds" if self.uds_path else "tcp-mtls"

    def call(self, method: str, request: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((method, request))
        return {"transport": self.transport(), "method": method, "request": request}

    def tls_context(self) -> ssl.SSLContext | None:
        if self.uds_path:
            return None
        context = ssl.create_default_context()
        context.mode = ssl.PROTOCOL_TLS_CLIENT
        context.check_hostname = True
        return context


def validate_spiffe_id(spiffe_id: str, trust_domain: str) -> bool:
    expected_prefix = f"{SPIFFE_PREFIX}{trust_domain}/"
    return spiffe_id.startswith(expected_prefix)

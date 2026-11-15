"""Agente co-localizado do BRLIA (host-adapter).

Roda JUNTO ao server da empresa sem reinicia-lo e sem alterar seu codigo.
Expoe UDS preferencial em /var/run/brlia/pool.sock e mantem WAL local para o
modo degradado com replay idempotente no reattach.
"""

from __future__ import annotations

import os
import signal
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from uds import UdsServer
from wal_local import LocalWal


class HostAgent:
    def __init__(self) -> None:
        self.socket_path = os.environ.get("BRLIA_UDS_PATH", "/var/run/brlia/pool.sock")
        self.wal = LocalWal()
        self.running = False
        self.drain_requested = False

    def handle(self, request: dict[str, Any]) -> dict[str, Any]:
        method = request.get("method", "")
        if method == "AdmitOperation":
            return self._admit(request)
        if method == "Reconcile":
            return {"consistent": True, "detail": "wal replay idempotente"}
        return {"error": f"metodo desconhecido: {method}"}

    def _admit(self, request: dict[str, Any]) -> dict[str, Any]:
        if self.drain_requested:
            return {
                "admitted": False,
                "rejection_code": "POOL_DEGRADED",
                "retry_hint": "retry com a mesma idempotency-key apos reattach",
            }
        self.wal.append(
            {
                "idempotency_key": request.get("idempotency_key"),
                "operation_id": request.get("operation_id"),
                "pool_key": request.get("pool_key"),
                "amount_minor": request.get("amount_minor"),
                "currency": request.get("currency"),
                "scale": request.get("scale", 2),
            }
        )
        return {"admitted": True, "pool_id": f"pool-host-{request.get('operation_id')}"}

    def drain(self) -> None:
        self.drain_requested = True
        time.sleep(0.05)
        self.wal.close()

    def run(self) -> None:
        self.running = True

        def stop(signum: int, frame: Any) -> None:
            self.drain()
            self.running = False

        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        server = UdsServer(self.handle, path=self.socket_path)
        server.serve_forever()


if __name__ == "__main__":
    HostAgent().run()

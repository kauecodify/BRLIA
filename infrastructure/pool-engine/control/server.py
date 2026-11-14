"""Servidor do control plane em socket de controle separado (UDS)."""

from __future__ import annotations

import os
from pathlib import Path

import uvicorn

from control.app import create_app


def main() -> None:
    socket_path = os.environ.get("BRLIA_CONTROL_SOCKET", "/var/run/brlia/control.sock")
    Path(socket_path).parent.mkdir(parents=True, exist_ok=True)
    if os.path.exists(socket_path):
        os.unlink(socket_path)
    app = create_app()
    uvicorn.run(app, uds=socket_path, log_level="info")


if __name__ == "__main__":
    main()

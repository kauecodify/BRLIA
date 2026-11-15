"""Unix Domain Socket, caminho preferencial de integracao.

/var/run/brlia/pool.sock com permissao 0660 e grupo brlia. Sem ingress
publico e sem porta TCP no modo co-localizado.
"""

from __future__ import annotations

import grp
import json
import os
import socket
from pathlib import Path
from typing import Any

DEFAULT_SOCKET = "/var/run/brlia/pool.sock"
DEFAULT_GROUP = "brlia"


class UdsServer:
    def __init__(self, handler: Any, path: str = DEFAULT_SOCKET, group: str = DEFAULT_GROUP) -> None:
        self.handler = handler
        self.path = Path(path)
        self.group = group

    def start(self) -> socket.socket:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            self.path.unlink()
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(str(self.path))
        os.chmod(self.path, 0o660)
        try:
            gid = grp.getgrnam(self.group).gr_gid
            os.chown(self.path, -1, gid)
        except (KeyError, PermissionError):
            pass
        server.listen(128)
        return server

    def serve_forever(self) -> None:
        server = self.start()
        while True:
            conn, _ = server.accept()
            with conn:
                data = conn.recv(65536)
                if not data:
                    continue
                try:
                    request = json.loads(data.decode("utf-8"))
                    response = self.handler(request)
                    status = 200
                except Exception as exc:
                    response = {"error": str(exc)}
                    status = 500
                body = json.dumps(response).encode("utf-8")
                header = f"{status}\n".encode("utf-8")
                conn.sendall(header + body)


class UdsClient:
    def __init__(self, path: str = DEFAULT_SOCKET) -> None:
        self.path = path

    def call(self, request: dict[str, Any]) -> dict[str, Any]:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(5)
        client.connect(self.path)
        try:
            client.sendall(json.dumps(request).encode("utf-8"))
            chunks = []
            while True:
                chunk = client.recv(65536)
                if not chunk:
                    break
                chunks.append(chunk)
            raw = b"".join(chunks)
        finally:
            client.close()
        status, _, body = raw.partition(b"\n")
        return {"status": int(status or 500), "body": json.loads(body or b"{}")}

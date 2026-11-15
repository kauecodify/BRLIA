"""Testes de co-localizacao: UDS, mTLS/SPIFFE, attach sem restart, degraded."""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path

INFRA = Path(__file__).resolve().parents[2] / "infrastructure"
sys.path.insert(0, str(INFRA / "host-adapter"))
sys.path.insert(0, str(INFRA / "auth-service"))

from uds import UdsClient, UdsServer  # noqa: E402
from mtls import GrpcChannelFactory, validate_spiffe_id  # noqa: E402
from wal_local import LocalWal  # noqa: E402
from app.scopes import scope_for, authorize  # noqa: E402


class TestUds(unittest.TestCase):
    def test_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = f"{tmp}/pool.sock"
            server = UdsServer(lambda req: {"admitted": True, "pool_id": "pool-1"}, path=path, group="root")
            ready = threading.Event()

            def serve() -> None:
                sock = server.start()
                ready.set()
                conn, _ = sock.accept()
                with conn:
                    data = conn.recv(65536)
                    response = server.handler(json.loads(data.decode("utf-8")))
                    conn.sendall(b"200\n" + json.dumps(response).encode("utf-8"))

            thread = threading.Thread(target=serve, daemon=True)
            thread.start()
            ready.wait(2)
            client = UdsClient(path)
            result = client.call({"method": "AdmitOperation", "idempotency_key": "k1"})
            self.assertEqual(result["status"], 200)
            self.assertTrue(result["body"]["admitted"])
            mode = (path and __import__("os").stat(path).st_mode) & 0o777
            self.assertEqual(mode, 0o660)


class TestMtls(unittest.TestCase):
    def test_uds_preferred(self) -> None:
        factory = GrpcChannelFactory(uds_path="/var/run/brlia/pool.sock", tcp_target=None, spiffe_id=None)
        self.assertEqual(factory.transport(), "uds")
        self.assertIsNone(factory.tls_context())

    def test_tcp_requires_spiffe(self) -> None:
        with self.assertRaises(ValueError):
            GrpcChannelFactory(uds_path=None, tcp_target="pool:443", spiffe_id=None)
        with self.assertRaises(ValueError):
            GrpcChannelFactory(uds_path=None, tcp_target="pool:443", spiffe_id="not-spiffe")
        factory = GrpcChannelFactory(
            uds_path=None,
            tcp_target="pool:443",
            spiffe_id="spiffe://brlia.local/host/agent",
        )
        self.assertEqual(factory.transport(), "tcp-mtls")
        self.assertIsNotNone(factory.tls_context())

    def test_spiffe_validation(self) -> None:
        self.assertTrue(validate_spiffe_id("spiffe://brlia.local/ns/edge", "brlia.local"))
        self.assertFalse(validate_spiffe_id("spiffe://other.local/ns", "brlia.local"))


class TestAttachWithoutRestart(unittest.TestCase):
    def test_agent_admit_and_drain(self) -> None:
        from agent import HostAgent

        with tempfile.TemporaryDirectory() as tmp:
            import os

            os.environ["BRLIA_WAL_PATH"] = f"{tmp}/host.wal"
            agent = HostAgent()
            first = agent.handle({"method": "AdmitOperation", "operation_id": "op-1", "idempotency_key": "k1", "amount_minor": 100})
            self.assertTrue(first["admitted"])
            duplicate = agent.handle({"method": "AdmitOperation", "operation_id": "op-1", "idempotency_key": "k1", "amount_minor": 100})
            self.assertTrue(duplicate["admitted"])
            agent.drain()
            rejected = agent.handle({"method": "AdmitOperation", "operation_id": "op-2", "idempotency_key": "k2", "amount_minor": 100})
            self.assertEqual(rejected["rejection_code"], "POOL_DEGRADED")
            wal = LocalWal(path=f"{tmp}/host.wal")
            records = wal.replay()
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["idempotency_key"], "k1")


class TestDegradedReplay(unittest.TestCase):
    def test_replay_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            wal = LocalWal(path=f"{tmp}/pool.wal")
            record = {"idempotency_key": "k-1", "pool_id": "pool-9", "amount_minor": 500}
            wal.append(record)
            wal.append(record)
            wal.append(record)
            records = wal.replay()
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["pool_id"], "pool-9")

    def test_expired_after_60s(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            wal = LocalWal(path=f"{tmp}/pool.wal")
            wal.append({"idempotency_key": "k-old", "buffered_at": 0})
            wal.append({"idempotency_key": "k-new"})
            expired = wal.expired(60)
            self.assertEqual([r["idempotency_key"] for r in expired], ["k-old"])


class TestScopes(unittest.TestCase):
    def test_scope_per_mode(self) -> None:
        for mode in ("sidecar", "daemonset", "standalone", "managed"):
            scope = scope_for("br", mode)
            self.assertTrue(authorize([scope], "br", mode))
        self.assertFalse(authorize([], "br", "sidecar"))
        with self.assertRaises(ValueError):
            scope_for("br", "cluster")


if __name__ == "__main__":
    unittest.main()

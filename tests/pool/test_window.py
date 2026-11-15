"""Testes da janela deterministica de 1 ms (implementacao de referencia)."""

from __future__ import annotations

import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "infrastructure" / "pool-engine"))

from clock import CLOCK_NAME, now_ns, window_index  # noqa: E402
from window import reference_window_manager  # noqa: E402


def op(i: int, amount: int = 1000, account: str = "A") -> dict:
    return {
        "operation_id": i,
        "idempotency_key": f"idem-{i}",
        "amount_minor": amount,
        "account": account,
        "currency": "BRL",
        "jurisdiction": "br",
    }


class TestWindow(unittest.TestCase):
    def test_clock_is_monotonic_raw(self) -> None:
        self.assertEqual(CLOCK_NAME, "CLOCK_MONOTONIC_RAW")
        first = now_ns()
        second = now_ns()
        self.assertGreaterEqual(second, first)

    def test_window_index_tick_1ms(self) -> None:
        now = now_ns()
        self.assertEqual(window_index(now, 1), now // 1_000_000)

    def test_ops_in_same_window_share_pool(self) -> None:
        manager = reference_window_manager(tick_ms=1000)
        manager.admit(op(1))
        manager.admit(op(2))
        event = manager.close(manager.current_window + 1)
        self.assertIsNotNone(event)
        self.assertEqual(event["admitted_ops"], 2)

    def test_pool_id_deterministic(self) -> None:
        manager_a = reference_window_manager()
        manager_b = reference_window_manager()
        for manager in (manager_a, manager_b):
            manager.admit(op(7))
            manager.current_window = 42
        event_a = manager_a.close(43)
        event_b = manager_b.close(43)
        self.assertEqual(event_a["pool_id"], event_b["pool_id"])
        self.assertEqual(event_a["monotonic_window"], 42)

    def test_one_event_per_window(self) -> None:
        manager = reference_window_manager()
        manager.admit(op(1))
        event = manager.close(manager.current_window + 1)
        again = manager.close(manager.current_window + 1)
        self.assertIsNotNone(event)
        self.assertIsNone(again)

    def test_window_not_queue_not_batch_not_cache(self) -> None:
        manager = reference_window_manager()
        manager.admit(op(1))
        event = manager.close(manager.current_window + 1)
        self.assertNotIn("queue", event)
        self.assertNotIn("batch", event)
        self.assertNotIn("cache", event)
        self.assertEqual(event["clock"], "CLOCK_MONOTONIC_RAW")


if __name__ == "__main__":
    unittest.main()

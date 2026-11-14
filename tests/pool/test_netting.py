"""Testes do netting multilateral: K <= N, natureza compensacao, teto."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "infrastructure" / "pool-engine"))

from netting import reference_nettle  # noqa: E402
from liquidity import LiquidityCeiling  # noqa: E402


def op(i: int, amount: int, account: str) -> dict:
    return {
        "operation_id": i,
        "idempotency_key": f"idem-{i}",
        "amount_minor": amount,
        "account": account,
        "currency": "BRL",
    }


class TestNetting(unittest.TestCase):
    def test_k_le_n(self) -> None:
        ops = [op(1, 1000, "A"), op(2, 2000, "A"), op(3, 500, "B")]
        entries = reference_nettle(ops)
        self.assertLessEqual(len(entries), len(ops))
        self.assertEqual(len(entries), 2)

    def test_zero_net_removed(self) -> None:
        ops = [op(1, 1000, "A"), op(2, -1000, "A")]
        entries = reference_nettle(ops)
        self.assertEqual(len(entries), 0)

    def test_liquid_amount_is_net(self) -> None:
        ops = [op(1, 1000, "A"), op(2, 250, "A")]
        entries = reference_nettle(ops)
        self.assertEqual(entries[0]["amount_minor"], 1250)
        self.assertEqual(entries[0]["side"], "D")

    def test_nature_is_compensacao(self) -> None:
        entries = reference_nettle([op(1, 100, "A")])
        self.assertEqual(entries[0]["nature"], "compensacao")

    def test_origin_trail_present(self) -> None:
        entries = reference_nettle([op(1, 100, "A"), op(2, 100, "A")])
        self.assertEqual(entries[0]["origin_trail"], [1, 2])

    def test_liquidity_ceiling_fixed(self) -> None:
        ceiling = LiquidityCeiling()
        self.assertEqual(ceiling.ceiling_minor, 10_000_000_000)
        with self.assertRaises(ValueError):
            LiquidityCeiling(999)

    def test_netting_never_touches_capital(self) -> None:
        entries = reference_nettle([op(1, 500, "2.1.1.01")])
        self.assertEqual(entries[0]["nature"], "compensacao")


if __name__ == "__main__":
    unittest.main()

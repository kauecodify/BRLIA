"""Testes do seed de capital: genesis imutavel e partidas dobradas."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tests._paths import REPO_ROOT

from seed.verify_seed import (  # noqa: E402
    check_double_entry,
    check_pool_entries,
    load_genesis,
    parse_sql_entries,
    parse_treasury_ceiling,
    VerificationError,
)


class TestSeed(unittest.TestCase):
    def test_genesis_value(self) -> None:
        genesis = load_genesis()
        self.assertEqual(genesis["amount_minor"], 10_000_000_000)
        self.assertEqual(genesis["currency"], "BRL")
        self.assertEqual(genesis["scale"], 2)
        self.assertTrue(genesis["immutable"])

    def test_double_entry(self) -> None:
        entries = parse_sql_entries()
        check_double_entry(entries)
        debit = sum(e["amount_minor"] for e in entries if e["side"] == "D")
        credit = sum(e["amount_minor"] for e in entries if e["side"] == "C")
        self.assertEqual(debit, credit)
        self.assertEqual(debit, 10_000_000_000)

    def test_treasury_ceiling_matches_genesis(self) -> None:
        self.assertEqual(parse_treasury_ceiling(), 10_000_000_000)

    def test_pool_entry_cannot_be_capital(self) -> None:
        with self.assertRaises(VerificationError):
            check_pool_entries(
                [
                    {
                        "pool_id": "pool-x",
                        "nature": "capital",
                        "account": "1.1.1.01",
                        "side": "D",
                        "amount_minor": 100,
                    }
                ]
            )

    def test_pool_entry_compensacao_ok(self) -> None:
        check_pool_entries(
            [
                {
                    "pool_id": "pool-x",
                    "nature": "compensacao",
                    "account": "1.1.1.01",
                    "side": "D",
                    "amount_minor": 100,
                }
            ]
        )


if __name__ == "__main__":
    unittest.main()

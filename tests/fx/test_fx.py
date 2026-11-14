"""Testes do fx-engine: PTAX injetavel, spread, IOF-FX e arredondamento."""

from __future__ import annotations

import sys
import unittest
from decimal import Decimal
from pathlib import Path

import importlib.util

REPO = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("fx_quote", REPO / "infrastructure" / "fx-engine" / "app" / "quote.py")
_mod = importlib.util.module_from_spec(_spec)
sys.modules["fx_quote"] = _mod
_spec.loader.exec_module(_mod)

PtaxProvider = _mod.PtaxProvider
convert = _mod.convert
to_minor = _mod.to_minor


class TestFx(unittest.TestCase):
    def test_to_minor_round_half_even(self) -> None:
        self.assertEqual(to_minor(Decimal("1.005")), 100)
        self.assertEqual(to_minor(Decimal("1.015")), 102)

    def test_convert_preserves_original(self) -> None:
        provider = PtaxProvider("5.0000")
        result = convert(100_00, provider=provider, spread_bps=0, iof_pct="0")
        self.assertEqual(result["amount_minor_source"], 100_00)
        self.assertEqual(result["amount_minor_target"], 500_00)
        self.assertEqual(result["quote_trail"]["provider"], "PTAX-fixo-referencia")

    def test_spread_reduces_target(self) -> None:
        provider = PtaxProvider("5.0000")
        no_spread = convert(100_00, provider=provider, spread_bps=0, iof_pct="0")
        with_spread = convert(100_00, provider=provider, spread_bps=100, iof_pct="0")
        self.assertLess(with_spread["amount_minor_target"], no_spread["amount_minor_target"])

    def test_iof_increases_target(self) -> None:
        provider = PtaxProvider("5.0000")
        no_iof = convert(100_00, provider=provider, spread_bps=0, iof_pct="0")
        with_iof = convert(100_00, provider=provider, spread_bps=0, iof_pct="1.10")
        self.assertGreater(with_iof["amount_minor_target"], no_iof["amount_minor_target"])

    def test_quote_trail_fields(self) -> None:
        result = convert(100_00)
        for field in ("rate", "spread_bps", "iof_pct", "rounding"):
            self.assertIn(field, result["quote_trail"] | result)


if __name__ == "__main__":
    unittest.main()

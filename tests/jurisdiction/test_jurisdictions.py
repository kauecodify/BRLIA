"""Testes da camada configuravel de jurisdicoes."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import importlib.util

REPO = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("jurisdiction_loader", REPO / "infrastructure" / "jurisdiction-engine" / "app" / "loader.py")
_mod = importlib.util.module_from_spec(_spec)
sys.modules["jurisdiction_loader"] = _mod
_spec.loader.exec_module(_mod)

JURISDICTIONS = _mod.JURISDICTIONS
load_all = _mod.load_all
load_jurisdiction = _mod.load_jurisdiction


class TestJurisdictions(unittest.TestCase):
    def test_all_jurisdictions_load(self) -> None:
        data = load_all()
        self.assertEqual(set(data.keys()), set(JURISDICTIONS))

    def test_br_currency(self) -> None:
        br = load_jurisdiction("br")
        self.assertEqual(br["currency"], "BRL")
        self.assertEqual(br["scale"], 2)
        self.assertIn("PIX", br["payment_systems"])

    def test_minimum_capital_present(self) -> None:
        for name in JURISDICTIONS:
            data = load_jurisdiction(name)
            self.assertIn("minimum_capital_minor", data)

    def test_unknown_jurisdiction_fails(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_jurisdiction("xx")


if __name__ == "__main__":
    unittest.main()

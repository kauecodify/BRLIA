"""E2E: PIX -> pool -> FX -> pacs.008 -> camt.053, com genesis intacto."""

from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
INFRA = REPO / "infrastructure"
sys.path.insert(0, str(INFRA / "pool-engine"))


def load_module(slug: str, relative: str, name: str):
    path = INFRA / slug / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


decision = load_module("routing-engine", "app/decision.py", "e2e_routing_decision")
window_pkg = load_module("pool-engine", "window/__init__.py", "e2e_pool_window")
outbox_mod = load_module("pool-engine", "publish/outbox.py", "e2e_pool_outbox")
outbox_orch = load_module("transaction-orchestrator", "app/outbox.py", "e2e_orchestrator_outbox")
app_pkg = types.ModuleType("app")
app_pkg.outbox = outbox_orch
sys.modules["app"] = app_pkg
sys.modules["app.outbox"] = outbox_orch
saga_mod = load_module("transaction-orchestrator", "app/saga.py", "e2e_orchestrator_saga")
app_pkg.saga = saga_mod
sys.modules["app.saga"] = saga_mod
pool_consumer = load_module("transaction-orchestrator", "app/pool_consumer.py", "e2e_orchestrator_consumer")
settlement = load_module("settlement-engine", "app/settlement.py", "e2e_settlement")
ledger_mod = load_module("ledger", "app/ledger.py", "e2e_ledger")
quote = load_module("fx-engine", "app/quote.py", "e2e_fx_quote")
convert_mod = load_module("multi-currency-ledger", "app/convert.py", "e2e_mc_convert")
worm_mod = load_module("audit-trail", "app/worm.py", "e2e_audit_worm")


class TestE2E(unittest.TestCase):
    def test_pix_to_pool_to_fx_to_iso20022(self) -> None:
        routed = decision.route(
            {
                "operation_id": "op-1",
                "idempotency_key": "e2e-1",
                "country": "BR",
                "currency": "BRL",
                "fx": True,
            }
        )
        self.assertIn(routed["decision"], ("br_intl", "fx"))
        self.assertIn("pool_key", routed)

        manager = window_pkg.reference_window_manager(tick_ms=1000)
        base = {
            "currency": "BRL",
            "jurisdiction": routed["pool_key"]["jurisdiction"],
        }
        manager.admit({**base, "operation_id": "op-1", "idempotency_key": "e2e-1", "amount_minor": 100_000, "account": "pix-acct-1", "leg": "pix"})
        manager.admit({**base, "operation_id": "op-2", "idempotency_key": "e2e-2", "amount_minor": -30_000, "account": "pix-acct-1", "leg": "fx"})
        window_event = manager.close(manager.current_window + 1)
        self.assertEqual(window_event["admitted_ops"], 2)
        self.assertEqual(window_event["netting"]["liquid_count"], 1)
        self.assertEqual(window_event["netting"]["liquid_entries"][0]["amount_minor"], 70_000)

        event = outbox_mod.build_pool_closed_event(window_event)
        self.assertEqual(event["event_type"], "pool.closed.v1")
        self.assertEqual(event["pool_key"]["functional_currency"], "BRL")
        self.assertIn("pool_id", event)

        consumer = pool_consumer.PoolClosedConsumer(outbox_orch.Outbox(spool_dir="/tmp/brlia-e2e-outbox"))
        accepted = consumer.handle(event)
        self.assertEqual(accepted["status"], "accepted")
        duplicated = consumer.handle(event)
        self.assertEqual(duplicated["status"], "duplicated")

        engine = settlement.SettlementEngine()
        result = engine.settle(event["pool_id"], event["netting"]["liquid_entries"])
        self.assertEqual(result["status"], "settled")

        ledger = ledger_mod.Ledger()
        entry = ledger.post(
            {
                "entry_id": "e2e-entry-1",
                "correlation_id": "e2e-1",
                "account": "pix-acct-1",
                "side": "D",
                "amount_minor": 70_000,
                "currency": "BRL",
                "scale": 2,
                "nature": "compensacao",
                "pool_id": event["pool_id"],
                "idempotency_key": "e2e-1",
            }
        )
        self.assertTrue(entry["entry_hash"])
        self.assertTrue(ledger.verify_chain())

        fx = quote.convert(100_00, spread_bps=10, iof_pct="1.10")
        self.assertEqual(fx["source_currency"], "USD")
        self.assertEqual(fx["target_currency"], "BRL")
        self.assertIn("quote_trail", fx)

        converted = convert_mod.convert_entry(
            {"amount_minor": 70_000, "currency": "BRL", "scale": 2},
            rate="0.2000",
            functional_currency="USD",
        )
        self.assertTrue(converted["original"]["preserved"])
        self.assertEqual(converted["functional"]["currency"], "USD")

        worm = worm_mod.WormLog(path="/tmp/brlia-e2e-audit.worm")
        record = worm.record_pool_close(event["pool_id"], event["composition_hash"], event["window_seq"])
        self.assertEqual(record["pool_id"], event["pool_id"])

        for message in ("pain.001", "pacs.008", "camt.053"):
            xsd = REPO / "configs" / "iso20022" / f"{message}.xsd"
            self.assertTrue(xsd.exists(), f"XSD ausente: {message}")

    def test_genesis_untouched_by_pool(self) -> None:
        sys.path.insert(0, str(REPO))
        from seed.verify_seed import load_genesis

        genesis = load_genesis()
        self.assertEqual(genesis["amount_minor"], 10_000_000_000)
        ledger = ledger_mod.Ledger()
        with self.assertRaises(ValueError):
            ledger.post(
                {
                    "entry_id": "bad-1",
                    "correlation_id": "pool-1",
                    "account": "2.1.1.01",
                    "side": "C",
                    "amount_minor": 100,
                    "currency": "BRL",
                    "scale": 2,
                    "nature": "operacao",
                    "pool_id": "pool-1",
                    "idempotency_key": "k-1",
                }
            )


if __name__ == "__main__":
    unittest.main()

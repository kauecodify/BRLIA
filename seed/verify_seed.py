#!/usr/bin/env python3
"""Verificacao do seed de capital do BRLIA.

Reconcilia tres fontes: seed/genesis.json, o snapshot de ledger_entries e a
politica de treasury (liquidity_ceiling_minor). Sai 0 apenas se as tres fontes
baterem centavo a centavo, o genesis estiver intacto e nenhum lancamento com
pool_id tiver natureza de capital.

Uso:
    python3 seed/verify_seed.py [--snapshot seed/ledger_snapshot.example.json]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GENESIS_PATH = REPO_ROOT / "seed" / "genesis.json"
ENTRIES_SQL_PATH = REPO_ROOT / "seed" / "genesis_entries.sql"
TREASURY_POLICY_PATH = REPO_ROOT / "seed" / "treasury_policy.yaml"

EXPECTED_AMOUNT_MINOR = 10_000_000_000
EXPECTED_CURRENCY = "BRL"
EXPECTED_SCALE = 2
CAPITAL_ACCOUNT = "2.1.1.01"


class VerificationError(Exception):
    pass


def load_genesis() -> dict:
    if not GENESIS_PATH.exists():
        raise VerificationError(f"genesis ausente: {GENESIS_PATH}")
    genesis = json.loads(GENESIS_PATH.read_text(encoding="utf-8"))
    if genesis.get("amount_minor") != EXPECTED_AMOUNT_MINOR:
        raise VerificationError(
            f"amount_minor do genesis difere de {EXPECTED_AMOUNT_MINOR}"
        )
    if genesis.get("currency") != EXPECTED_CURRENCY or genesis.get("scale") != EXPECTED_SCALE:
        raise VerificationError("moeda ou scale do genesis divergem de BRL/2")
    if genesis.get("immutable") is not True:
        raise VerificationError("genesis marcado como mutavel")
    return genesis


def parse_sql_entries() -> list[dict]:
    if not ENTRIES_SQL_PATH.exists():
        raise VerificationError(f"genesis_entries.sql ausente: {ENTRIES_SQL_PATH}")
    text = ENTRIES_SQL_PATH.read_text(encoding="utf-8")
    pattern = re.compile(
        r"\(\s*'([^']+)'\s*,\s*'([^']+)'\s*,\s*'([^']+)'\s*,\s*'[^']*'\s*,\s*"
        r"'([DC])'\s*,\s*(\d+)::bigint\s*,\s*'([A-Z]{3})'\s*,\s*(\d+)\s*,\s*'([^']+)'",
        re.VERBOSE,
    )
    entries = []
    for match in pattern.finditer(text):
        entries.append(
            {
                "correlation_id": match.group(1),
                "entry_id": match.group(2),
                "account": match.group(3),
                "side": match.group(4),
                "amount_minor": int(match.group(5)),
                "currency": match.group(6),
                "scale": int(match.group(7)),
                "nature": match.group(8),
                "pool_id": None,
            }
        )
    if not entries:
        raise VerificationError("nenhum lancamento parseado de genesis_entries.sql")
    return entries


def parse_treasury_ceiling() -> int:
    if not TREASURY_POLICY_PATH.exists():
        raise VerificationError(f"treasury_policy ausente: {TREASURY_POLICY_PATH}")
    text = TREASURY_POLICY_PATH.read_text(encoding="utf-8")
    match = re.search(r"^liquidity_ceiling_minor:\s*(\d+)$", text, re.MULTILINE)
    if not match:
        raise VerificationError("liquidity_ceiling_minor ausente em treasury_policy.yaml")
    return int(match.group(1))


def load_snapshot(path: Path | None) -> list[dict]:
    if path is None:
        return []
    if not path.exists():
        raise VerificationError(f"snapshot ausente: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("ledger_entries", [])


def check_double_entry(entries: list[dict]) -> None:
    debit = sum(e["amount_minor"] for e in entries if e["side"] == "D")
    credit = sum(e["amount_minor"] for e in entries if e["side"] == "C")
    if debit != credit:
        raise VerificationError(f"partidas dobradas nao fecham: D={debit} C={credit}")
    if debit != EXPECTED_AMOUNT_MINOR:
        raise VerificationError(
            f"soma de debitos difere do genesis: {debit} != {EXPECTED_AMOUNT_MINOR}"
        )


def check_pool_entries(entries: list[dict]) -> None:
    for entry in entries:
        if entry.get("pool_id"):
            if entry.get("nature") != "compensacao":
                raise VerificationError(
                    f"lancamento com pool_id {entry.get('pool_id')} tem natureza "
                    f"'{entry.get('nature')}', esperado 'compensacao'"
                )
            if entry.get("account") == CAPITAL_ACCOUNT and entry.get("side") == "C":
                raise VerificationError(
                    "lancamento do pool credita Capital Social: genesis mutado"
                )
            if entry.get("amount_minor", 0) > parse_treasury_ceiling():
                raise VerificationError(
                    "lancamento do pool excede liquidity_ceiling_minor"
                )


def check_sources(genesis_total: int, sql_total: int, snapshot_total: int | None) -> None:
    if sql_total != genesis_total:
        raise VerificationError(
            f"genesis_entries.sql ({sql_total}) difere do genesis ({genesis_total})"
        )
    if snapshot_total is not None and snapshot_total != genesis_total:
        raise VerificationError(
            f"snapshot do ledger ({snapshot_total}) difere do genesis ({genesis_total})"
        )
    ceiling = parse_treasury_ceiling()
    if ceiling != genesis_total:
        raise VerificationError(
            f"liquidity_ceiling_minor ({ceiling}) difere do genesis ({genesis_total})"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Verificacao do seed BRLIA")
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=REPO_ROOT / "seed" / "ledger_snapshot.example.json",
        help="snapshot JSON de ledger_entries exportado do banco",
    )
    args = parser.parse_args()

    try:
        genesis = load_genesis()
        genesis_total = sum(
            e["amount_minor"] for e in genesis["entries"] if e["side"] == "D"
        )
        sql_entries = parse_sql_entries()
        check_double_entry(sql_entries)
        sql_total = sum(e["amount_minor"] for e in sql_entries if e["side"] == "D")
        snapshot_entries = load_snapshot(args.snapshot)
        if snapshot_entries:
            check_pool_entries(snapshot_entries)
            snapshot_total = sum(
                e["amount_minor"]
                for e in snapshot_entries
                if e.get("correlation_id") == genesis["correlation_id"]
                and e.get("side") == "D"
            )
        else:
            snapshot_total = None
        check_sources(genesis_total, sql_total, snapshot_total)
    except VerificationError as exc:
        print(f"FALHA: {exc}", file=sys.stderr)
        return 1

    print("OK: genesis, genesis_entries.sql, snapshot e treasury_policy batem centavo a centavo.")
    print("OK: nenhum lancamento com pool_id mutou o genesis.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

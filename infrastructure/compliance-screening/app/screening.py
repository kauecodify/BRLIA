"""Screening: OFAC/SDN, PEP, KYC/KYB/KYT e Travel Rule (FATF R.16)."""

from __future__ import annotations

from typing import Any

OFAC_SDN = ["sanctioned-entity-example"]
PEP_LIST = ["pep-entity-example"]


def screen(payload: dict[str, Any]) -> dict[str, Any]:
    name = str(payload.get("counterparty_name", "")).lower()
    hits = []
    if any(entry in name for entry in OFAC_SDN):
        hits.append("OFAC/SDN")
    if any(entry in name for entry in PEP_LIST):
        hits.append("PEP")
    travel_rule_required = int(payload.get("amount_minor", 0)) >= 1_000_000_00
    return {
        "hits": hits,
        "decision": "block" if "OFAC/SDN" in hits else "clear",
        "travel_rule": {
            "required": travel_rule_required,
            "standard": "FATF R.16",
            "originator_beneficiary_data": bool(payload.get("originator") and payload.get("beneficiary")),
        },
    }

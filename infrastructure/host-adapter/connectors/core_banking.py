"""Conector core banking: somente leitura."""

from __future__ import annotations

from typing import Any

from connectors.base import ReadOnlyConnector


class CoreBankingConnector(ReadOnlyConnector):
    name = "core-banking"

    def read(self, query: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if self.source is None:
            return []
        return list(self.source.get("core-banking", []))

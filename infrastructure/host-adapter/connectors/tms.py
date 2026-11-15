"""Conector TMS: somente leitura."""

from __future__ import annotations

from typing import Any

from connectors.base import ReadOnlyConnector


class TmsConnector(ReadOnlyConnector):
    name = "tms"

    def read(self, query: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if self.source is None:
            return []
        return list(self.source.get("tms", []))

"""Conector PIX API: somente leitura, idempotencia por endToEndId."""

from __future__ import annotations

from typing import Any

from connectors.base import ReadOnlyConnector


class PixApiConnector(ReadOnlyConnector):
    name = "pix-api"
    idempotency_field = "endToEndId"

    def read(self, query: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if self.source is None:
            return []
        return list(self.source.get("pix-api", []))

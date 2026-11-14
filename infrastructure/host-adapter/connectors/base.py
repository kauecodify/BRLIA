"""Base dos conectores somente leitura."""

from __future__ import annotations

from typing import Any


class ReadOnlyConnector:
    name = "base"
    read_only = True

    def __init__(self, source: Any | None = None) -> None:
        self.source = source
        self.writes_attempted = 0

    def read(self, query: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        raise NotImplementedError

    def write(self, *args: Any, **kwargs: Any) -> None:
        self.writes_attempted += 1
        raise PermissionError(
            f"conector {self.name} e somente leitura; escrita no host e proibida"
        )

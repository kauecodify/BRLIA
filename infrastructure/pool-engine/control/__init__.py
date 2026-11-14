"""Control plane do pool-engine.

FastAPI atende somente /health, /ready, /metrics e /config, em socket de
controle separado do hot path. Nenhum endpoint de admissao existe aqui.
"""

from __future__ import annotations

from control.app import create_app

__all__ = ["create_app"]

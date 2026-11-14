"""Publicacao do pool.closed.v1.

Um unico evento por janela, entregue ao transactional outbox de forma
assincrona. O evento e versionado em schemas/events/pool.closed.v1.json e o
audit-trail grava pool_id e hash da composicao em WORM.
"""

from __future__ import annotations

from publish.outbox import OutboxPublisher, build_pool_closed_event

__all__ = ["OutboxPublisher", "build_pool_closed_event"]

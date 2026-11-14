"""Saga com compensacao e transactional outbox.

Cada passo tem acao e compensacao; a compensacao e emitida como
saga.compensated.v1 no outbox. Toda escrita exige idempotency-key.
"""

from __future__ import annotations

from typing import Any, Callable

from app.outbox import Outbox


class SagaStep:
    def __init__(self, name: str, action: Callable[[dict[str, Any]], dict[str, Any]],
                 compensate: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        self.name = name
        self.action = action
        self.compensate = compensate


class Saga:
    def __init__(self, saga_id: str, outbox: Outbox) -> None:
        self.saga_id = saga_id
        self.outbox = outbox
        self.steps: list[SagaStep] = []
        self.completed: list[SagaStep] = []

    def add_step(self, step: SagaStep) -> None:
        self.steps.append(step)

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        for step in self.steps:
            try:
                context = step.action(context)
                self.completed.append(step)
            except Exception as exc:
                for done in reversed(self.completed):
                    done.compensate(context)
                self.outbox.publish(
                    {
                        "event_type": "saga.compensated.v1",
                        "saga_id": self.saga_id,
                        "operation_id": context.get("operation_id", ""),
                        "pool_id": context.get("pool_id", ""),
                        "reason": f"falha no passo {step.name}: {exc}",
                    }
                )
                raise
        return context

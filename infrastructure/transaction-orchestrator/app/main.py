"""Transaction orchestrator BRLIA: saga, outbox e consumo de pool.closed.v1."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import FastAPI, Request, Response

from app.outbox import Outbox
from app.pool_consumer import PoolClosedConsumer

app = FastAPI(title="transaction-orchestrator", version="2.1.0")
outbox = Outbox()
consumer = PoolClosedConsumer(outbox)


@app.middleware("http")
async def trace_context(request: Request, call_next: Any) -> Response:
    trace_id = request.headers.get("X-Trace-Id", str(uuid.uuid4()))
    request.state.trace_id = trace_id
    response: Response = await call_next(request)
    response.headers["X-Trace-Id"] = trace_id
    return response


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    return {"status": "ready"}


@app.get("/metrics")
def metrics() -> Response:
    return Response(content="sagas_total 0\npool_closed_consumed_total 0\n", media_type="text/plain")


@app.post("/pool.closed.v1")
def consume_pool_closed(event: dict[str, Any]) -> dict[str, Any]:
    return consumer.handle(event)

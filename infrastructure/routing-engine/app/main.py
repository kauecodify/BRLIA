"""Routing engine BRLIA: decide br | intl | fx | br_intl e emite pool_key
antes da orquestracao."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import FastAPI, Request, Response

from app.decision import route

app = FastAPI(title="routing-engine", version="2.1.0")


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
    return Response(
        content="routing_decisions_total 0\npool_keys_emitted_total 0\n",
        media_type="text/plain",
    )


@app.post("/route")
def route_operation(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("idempotency_key"):
        return {"error": "idempotency_key obrigatoria"}
    return route(payload)

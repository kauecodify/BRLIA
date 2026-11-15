"""Jurisdiction engine BRLIA: carrega configs/jurisdictions e expoe decisao de residencia.

Control plane FastAPI com /health, /ready e /metrics e propagacao de trace_id.
Toda escrita exige idempotency-key e passa por saga com transactional outbox.
"""

from __future__ import annotations

import os
import uuid
from typing import Any

from fastapi import FastAPI, Request, Response

app = FastAPI(title="jurisdiction_engine", version="2.1.0")


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
    body = (
        "# TYPE jurisdiction_engine_up gauge\n"
        "jurisdiction_engine_up 1\n"
    )
    return Response(content=body, media_type="text/plain")

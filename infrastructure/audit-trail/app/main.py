"""Audit trail BRLIA: WORM com hash encadeado e registro de pool_id."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import FastAPI, Request, Response

from app.worm import WormLog

app = FastAPI(title="audit-trail", version="2.1.0")
worm = WormLog()


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
        content=(
            f"audit_records_total {len(worm.records)}\n"
            f"audit_genesis_hash_mismatch_total {worm.genesis_hash_mismatches}\n"
        ),
        media_type="text/plain",
    )


@app.post("/records")
def append_record(record: dict[str, Any]) -> dict[str, Any]:
    return worm.append(record)

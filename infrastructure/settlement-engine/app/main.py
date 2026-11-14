"""Settlement engine BRLIA: consome lancamentos liquidos do pool."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import FastAPI, Request, Response

from app.settlement import SettlementEngine

app = FastAPI(title="settlement-engine", version="2.1.0")
engine = SettlementEngine()


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
    return Response(content=f"pools_settled_total {len(engine.settled)}\n", media_type="text/plain")


@app.post("/settle")
def settle(payload: dict[str, Any]) -> dict[str, Any]:
    return engine.settle(payload["pool_id"], payload.get("liquid_entries", []))

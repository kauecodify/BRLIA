"""Ledger BRLIA: partidas dobradas, hash-chain e genesis imutavel."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import FastAPI, Request, Response

from app.ledger import Ledger

app = FastAPI(title="ledger", version="2.1.0")
ledger = Ledger()


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
    return Response(content=f"ledger_entries_total {len(ledger.entries)}\n", media_type="text/plain")


@app.post("/entries")
def post_entry(entry: dict[str, Any]) -> dict[str, Any]:
    return ledger.post(entry)


@app.get("/verify")
def verify() -> dict[str, bool]:
    return {"chain_valid": ledger.verify_chain()}

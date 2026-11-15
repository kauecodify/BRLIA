"""Treasury service BRLIA: expoe liquidity_ceiling_minor (somente leitura).

O teto de referencia e 10000000000 minor units (R$ 100.000.000,00) e nunca e
debitado pelo pool. O genesis permanece imutavel.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import FastAPI, Request, Response

app = FastAPI(title="treasury-service", version="2.1.0")

LIQUIDITY_CEILING_MINOR = 10_000_000_000
MINIMUM_CAPITAL_MINOR = 1_000_000_000


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
            f"treasury_liquidity_available_minor {LIQUIDITY_CEILING_MINOR}\n"
            f"treasury_minimum_capital_minor {MINIMUM_CAPITAL_MINOR}\n"
        ),
        media_type="text/plain",
    )


@app.get("/liquidity/ceiling")
def liquidity_ceiling() -> dict[str, Any]:
    return {
        "liquidity_ceiling_minor": LIQUIDITY_CEILING_MINOR,
        "currency": "BRL",
        "scale": 2,
        "readonly": True,
        "genesis_mutable": False,
    }

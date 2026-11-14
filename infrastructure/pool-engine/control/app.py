"""Control plane FastAPI do pool-engine (somente /health /ready /metrics /config)."""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, Response

try:
    import brlia_pool_core as _core
    CORE_COMPILED = _core is not None
except ImportError:
    _core = None
    CORE_COMPILED = False

from clock import CLOCK_NAME, now_ns, window_index


def create_app() -> FastAPI:
    app = FastAPI(title="brlia-pool-engine-control", version="2.1.0")
    state: dict[str, Any] = {"ready": CORE_COMPILED, "rejected_total": 0, "window_ops": 0}

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {"status": "ok", "clock": CLOCK_NAME, "core_compiled": CORE_COMPILED}

    @app.get("/ready")
    def ready() -> dict[str, Any]:
        if not state["ready"]:
            return Response(
                content='{"status": "not-ready", "reason": "core compilado ausente"}',
                media_type="application/json",
                status_code=503,
            )
        return {"status": "ready", "clock": CLOCK_NAME}

    @app.get("/metrics")
    def metrics() -> str:
        lines = [
            "# HELP pool_window_ops operacoes admitidas por janela",
            "# TYPE pool_window_ops counter",
            f"pool_window_ops {state['window_ops']}",
            "# HELP pool_rejected_total rejeicoes POOL_FULL",
            "# TYPE pool_rejected_total counter",
            f"pool_rejected_total {state['rejected_total']}",
            "# HELP pool_admit_latency_seconds limite configurado de admit (p99 1ms)",
            "# TYPE pool_admit_latency_seconds gauge",
            f"pool_admit_latency_seconds_limit {{quantile=\"0.99\"}} 0.001",
            "# HELP pool_close_latency_seconds limite configurado de close+netting (p99 3ms)",
            "# TYPE pool_close_latency_seconds gauge",
            f"pool_close_latency_seconds_limit {{quantile=\"0.99\"}} 0.003",
        ]
        return "\n".join(lines) + "\n"

    @app.get("/config")
    def config() -> dict[str, Any]:
        return {
            "deploy_mode": os.environ.get("BRLIA_DEPLOY_MODE", "sidecar"),
            "tick_ms": int(os.environ.get("BRLIA_POOL_TICK_MS", "1")),
            "uds_path": os.environ.get("BRLIA_UDS_PATH", "/var/run/brlia/pool.sock"),
            "queue_depth": int(os.environ.get("BRLIA_POOL_QUEUE_DEPTH", "65536")),
            "watermark_ms": int(os.environ.get("BRLIA_POOL_WATERMARK_MS", "5")),
            "max_ops_per_window": int(os.environ.get("BRLIA_POOL_MAX_OPS_PER_WINDOW", "4096")),
            "clock": CLOCK_NAME,
        }

    return app

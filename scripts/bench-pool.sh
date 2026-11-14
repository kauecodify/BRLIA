#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
echo "bench do pool: 100.000 operacoes, histograma HDR, falha se p99(close+netting) > 5ms"
echo "os limites sao os configurados em configs/pool/slo.yaml; nenhum valor e pre-medido"
exec python3 "${REPO_ROOT}/tests/pool/bench_pool.py" "$@"

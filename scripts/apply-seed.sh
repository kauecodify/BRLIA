#!/usr/bin/env bash
set -euo pipefail
# Aplica o genesis de R$ 100.000.000,00 de forma idempotente.
# Falha se correlation_id ja existir.

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CORRELATION_ID="seed-genesis-0000000000000001"

PGHOST="${BRLIA_PG_HOST:-localhost}"
PGPORT="${BRLIA_PG_PORT:-5432}"
PGDATABASE="${BRLIA_PG_DB:-brlia}"
PGUSER="${BRLIA_PG_USER:-brlia}"
export PGHOST PGPORT PGDATABASE PGUSER

export PGPASSWORD="${BRLIA_PG_PASSWORD:-}"

EXISTING="$(psql -Atqc "SELECT count(*) FROM ledger_entries WHERE correlation_id = '${CORRELATION_ID}';")"
if [[ "${EXISTING}" != "0" ]]; then
  echo "ERRO: correlation_id ${CORRELATION_ID} ja existe; seed nao e reaplicado" >&2
  exit 1
fi

psql -v ON_ERROR_STOP=1 -f "${REPO_ROOT}/seed/genesis_entries.sql"
python3 "${REPO_ROOT}/seed/verify_seed.py"
echo "seed aplicado: R$ 100.000.000,00 em partidas dobradas"

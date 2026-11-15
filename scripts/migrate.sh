#!/usr/bin/env bash
set -euo pipefail
PGHOST="${BRLIA_PG_HOST:-localhost}" \
PGPORT="${BRLIA_PG_PORT:-5432}" \
PGDATABASE="${BRLIA_PG_DB:-brlia}" \
PGUSER="${BRLIA_PG_USER:-brlia}" \
PGPASSWORD="${BRLIA_PG_PASSWORD:-}" \
psql -v ON_ERROR_STOP=1 -f "$(dirname "$0")/init-db.sql"
echo "migracoes aplicadas"

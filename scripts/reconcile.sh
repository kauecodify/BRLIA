#!/usr/bin/env bash
set -euo pipefail
# Reconcilia genesis, pool e ledger centavo a centavo.
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

PGHOST="${BRLIA_PG_HOST:-localhost}" \
PGPORT="${BRLIA_PG_PORT:-5432}" \
PGDATABASE="${BRLIA_PG_DB:-brlia}" \
PGUSER="${BRLIA_PG_USER:-brlia}" \
PGPASSWORD="${BRLIA_PG_PASSWORD:-}" \
psql -Atqc "
  SELECT json_build_object(
    'ledger_entries', (
      SELECT COALESCE(json_agg(row_to_json(e)), '[]'::json)
      FROM (
        SELECT correlation_id, entry_id, account, side, amount_minor, currency, scale, nature, pool_id
        FROM ledger_entries ORDER BY created_at
      ) e
    )
  );
" > "${REPO_ROOT}/seed/ledger_snapshot.json"

python3 "${REPO_ROOT}/seed/verify_seed.py" --snapshot "${REPO_ROOT}/seed/ledger_snapshot.json"
echo "reconciliacao concluida"

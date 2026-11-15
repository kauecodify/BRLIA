#!/usr/bin/env bash
set -euo pipefail
# Varredura estatica: sem cliente Redis/PostgreSQL/Kafka em core, window,
# netting e clock do pool-engine.
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
HOT="${REPO_ROOT}/infrastructure/pool-engine"
VIOLATIONS=0
for pattern in redis psycopg asyncpg postgres kafka confluent; do
  if grep -rni "${pattern}" "${HOT}/core" "${HOT}/window" "${HOT}/netting" "${HOT}/clock" \
      --include='*.py' --include='*.rs' --include='*.toml' >/dev/null 2>&1; then
    echo "VIOLACAO: cliente de rede '${pattern}' no hot path" >&2
    VIOLATIONS=1
  fi
done
if [[ ${VIOLATIONS} -eq 0 ]]; then
  echo "OK: nenhum cliente Redis/Postgres/Kafka em core, window, netting e clock"
fi
exit ${VIOLATIONS}

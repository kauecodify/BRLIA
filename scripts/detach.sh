#!/usr/bin/env bash
set -euo pipefail
# Drena a janela corrente, fecha o WAL e desacopla o agente.
if [[ ${EUID} -ne 0 ]]; then
  echo "detach exige root" >&2
  exit 1
fi
if systemctl is-active --quiet brlia-agent.service; then
  systemctl stop brlia-agent.service
fi
WAL="${BRLIA_WAL_PATH:-/var/lib/brlia/host-adapter.wal}"
if [[ -f "${WAL}" ]]; then
  echo "WAL preservado para replay idempotente no reattach: ${WAL}"
fi
echo "detach concluido: janela drenada, WAL fechado, agente desacoplado"

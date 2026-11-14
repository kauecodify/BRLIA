#!/usr/bin/env bash
set -euo pipefail
# Acopla o agente ao host SEM reiniciar o processo da empresa, SEM alterar
# codigo do ERP/core banking/TMS, SEM ingress publico e SEM migracao de dados.
MODE="standalone"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode) MODE="$2"; shift 2 ;;
    *) shift ;;
  esac
done

if [[ ${EUID} -ne 0 ]]; then
  echo "attach exige root para criar /var/run/brlia e o grupo brlia" >&2
  exit 1
fi

getent group brlia >/dev/null || groupadd brlia
install -d -g brlia -m 0770 /var/run/brlia

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
case "$MODE" in
  standalone)
    bash "${REPO_ROOT}/deploy/onprem/install.sh"
    systemctl start brlia-agent.service
    ;;
  sidecar|daemonset|managed)
    echo "modo ${MODE}: aplique o manifesto correspondente em deploy/ e mantenha o host intacto"
    ;;
  *) echo "modo invalido: $MODE" >&2; exit 1 ;;
esac

echo "attach concluido em modo ${MODE}: UDS /var/run/brlia/pool.sock, host nao reiniciado"

#!/usr/bin/env bash
set -euo pipefail
# Instala o agente co-localizado em servidor proprio (systemd).
# Nao reinicia processos do host e nao altera codigo do ERP, core banking ou TMS.

if [[ ${EUID} -ne 0 ]]; then
  echo "execute com root" >&2
  exit 1
fi

getent group brlia >/dev/null || groupadd brlia
id -u brlia >/dev/null 2>&1 || useradd -r -g brlia -d /var/lib/brlia -s /usr/sbin/nologin brlia

install -d -o brlia -g brlia -m 0750 /var/lib/brlia
install -d -o brlia -g brlia -m 0770 /var/run/brlia

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
install -d -o brlia -g brlia -m 0755 /opt/brlia/host-adapter
cp -r "${REPO_ROOT}/infrastructure/host-adapter/." /opt/brlia/host-adapter/
install -m 0644 "${REPO_ROOT}/deploy/onprem/systemd/brlia-agent.service" /etc/systemd/system/brlia-agent.service

systemctl daemon-reload
systemctl enable brlia-agent.service
echo "instalado. para acoplar sem restart do host: systemctl start brlia-agent"

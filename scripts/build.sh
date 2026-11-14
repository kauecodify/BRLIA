#!/usr/bin/env bash
set -euo pipefail
# Build multi-arch incluindo o binario do nucleo do pool.
PLATFORMS="linux/amd64,linux/arm64"
docker buildx build --platform "$PLATFORMS" -t brlia/pool-engine:2.1.0 infrastructure/pool-engine
docker buildx build --platform "$PLATFORMS" -t brlia/host-adapter:2.1.0 infrastructure/host-adapter
for svc in routing-engine transaction-orchestrator settlement-engine ledger multi-currency-ledger \
           fx-engine jurisdiction-engine treasury-service risk-engine compliance-screening \
           escrow-manager auth-service notification-service file-processor audit-trail \
           reporting-regulatorio; do
  docker buildx build --platform "$PLATFORMS" -t "brlia/${svc}:2.1.0" "infrastructure/${svc}"
done
echo "build multi-arch concluido"

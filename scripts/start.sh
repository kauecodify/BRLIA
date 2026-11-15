#!/usr/bin/env bash
set -euo pipefail
# Sobe a plataforma. Perfis: br | intl | all | colocated.
PROFILE="all"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile) PROFILE="$2"; shift 2 ;;
    *) echo "uso: start.sh --profile br|intl|all|colocated" >&2; exit 1 ;;
  esac
done
COMPOSE_FILES=(-f docker-compose.yml)
case "$PROFILE" in
  colocated) COMPOSE_FILES+=(-f docker-compose.colocated.yml) ;;
  br|intl|all) ;;
  *) echo "perfil invalido: $PROFILE" >&2; exit 1 ;;
esac
exec docker compose "${COMPOSE_FILES[@]}" --profile "$PROFILE" up -d

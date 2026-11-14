#!/usr/bin/env bash
set -euo pipefail
docker compose -f docker-compose.yml -f docker-compose.colocated.yml --profile all --profile colocated down

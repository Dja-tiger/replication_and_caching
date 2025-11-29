#!/usr/bin/env bash
# Promote a standby to primary inside the container
# Usage: ./tools/promote_replica.sh pg-replica2

set -euo pipefail
TARGET_CONTAINER="${1:-}" || true
if [ -z "$TARGET_CONTAINER" ]; then
  echo "Usage: $0 <container_name>"
  exit 1
fi

docker exec "$TARGET_CONTAINER" bash -c "pg_ctl -D $PGDATA promote"

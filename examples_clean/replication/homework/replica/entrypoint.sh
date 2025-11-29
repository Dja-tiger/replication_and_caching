#!/usr/bin/env bash
set -euo pipefail

PRIMARY_HOST="${PRIMARY_HOST:-primary}"
REPLICATION_USER="${REPLICATION_USER:-replicator}"
REPLICATION_PASSWORD="${REPLICATION_PASSWORD:-replicate_me}"

if [ -z "${PGDATA:-}" ]; then
  export PGDATA="/var/lib/postgresql/data"
fi

if [ ! -s "$PGDATA/PG_VERSION" ]; then
  until pg_isready -h "$PRIMARY_HOST" -p 5432 -U "$REPLICATION_USER"; do
    echo "Waiting for primary $PRIMARY_HOST..."
    sleep 1
  done

  PGPASSWORD="$REPLICATION_PASSWORD" pg_basebackup -h "$PRIMARY_HOST" -D "$PGDATA" -U "$REPLICATION_USER" -Fp -Xs -P -R \
    -C -S "${HOSTNAME}_slot"

  cat >> "$PGDATA/postgresql.auto.conf" <<CONFIG
hot_standby = on
primary_slot_name = '${HOSTNAME}_slot'
primary_conninfo = 'host=$PRIMARY_HOST port=5432 user=$REPLICATION_USER password=$REPLICATION_PASSWORD application_name=${HOSTNAME}'
CONFIG
fi

exec postgres -c hot_standby_feedback=on -c shared_buffers=256MB

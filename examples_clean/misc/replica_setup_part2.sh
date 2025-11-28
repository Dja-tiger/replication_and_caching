# Настройка Replica (2/2)

# Базовый бэкап с мастера
pg_basebackup -h master.db -U replicator \
  -D /var/lib/postgresql/14/main -P -v \
  -R -X stream -C -S replica1

# standby.signal создаётся автоматически
# postgresql.auto.conf
primary_conninfo = 'host=master.db port=5432
  user=replicator password=secret'
primary_slot_name = 'replica1'
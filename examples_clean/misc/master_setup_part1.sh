# Настройка Master (1/2)

# postgresql.conf на мастере
wal_level = replica
max_wal_senders = 10
wal_keep_size = 1GB  # PostgreSQL 13+, ранее wal_keep_segments
hot_standby = on
archive_mode = on
archive_command = 'cp %p /archive/%f'

# pg_hba.conf
host replication replicator 10.0.0.0/24 md5
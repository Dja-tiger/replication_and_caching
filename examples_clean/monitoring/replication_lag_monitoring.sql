# Мониторинг lag

-- На master
SELECT client_addr, state,
       write_lag, flush_lag, replay_lag
FROM pg_stat_replication;

-- На replica
SELECT now() - pg_last_xact_replay_timestamp() AS lag;

-- Prometheus метрики
pg_replication_lag_seconds
pg_stat_replication_pg_wal_lsn_diff
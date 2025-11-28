# Настройка Sentinel (1/2)

# sentinel.conf
port 26379
sentinel monitor mymaster 10.0.0.1 6379 2
sentinel auth-pass mymaster strongpass
sentinel down-after-milliseconds mymaster 5000
sentinel parallel-syncs mymaster 1
sentinel failover-timeout mymaster 180000

# Запуск трёх Sentinel
redis-sentinel /etc/redis/sentinel1.conf
redis-sentinel /etc/redis/sentinel2.conf
redis-sentinel /etc/redis/sentinel3.conf
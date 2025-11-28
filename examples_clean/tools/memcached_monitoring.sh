# Memcached: мониторинг

# Статистика в реальном времени
watch 'echo "stats" | nc localhost 11211 | grep -E "get_|set_|bytes"'

# Анализ эффективности кэша
memcached-tool localhost:11211 stats | grep ratio
# get_hits / (get_hits + get_misses) > 90% - хорошо

# Топ ключей (требует отдельной настройки)
memcached-tool localhost:11211 dump | \
  awk '{print $2}' | sort | uniq -c | sort -rn | head -20

# Мониторинг через Prometheus
memcached_exporter --memcached.address="localhost:11211"

# Grafana dashboard для Техномира:
# - Hit ratio: > 95%
# - Evictions: < 1% от sets
# - Connection rate: < 1000/s
# - Response time: < 1ms
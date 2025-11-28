# Redis Cluster: шардирование

# Создание кластера (6 нод = 3 master + 3 replica)
redis-cli --cluster create \
  10.0.0.1:6379 10.0.0.2:6379 10.0.0.3:6379 \
  10.0.0.4:6379 10.0.0.5:6379 10.0.0.6:6379 \
  --cluster-replicas 1

# Проверка кластера
redis-cli --cluster check 10.0.0.1:6379

# Решардинг (перемещение слотов)
redis-cli --cluster reshard 10.0.0.1:6379 \
  --cluster-from node1_id \
  --cluster-to node2_id \
  --cluster-slots 1000
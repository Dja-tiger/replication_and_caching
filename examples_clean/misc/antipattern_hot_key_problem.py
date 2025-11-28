# Антипаттерн: Hot Key Problem

# ✅ Распределение нагрузки
def get_hot_key(key, replicas=10):
    # Добавляем случайный суффикс
    replica_key = f"{key}:r{random.randint(0, replicas-1)}"
    return cache.get(replica_key)

# При записи обновляем все реплики
def set_hot_key(key, value, replicas=10):
    pipe = redis.pipeline()
    for i in range(replicas):
        pipe.set(f"{key}:r{i}", value)
    pipe.execute()
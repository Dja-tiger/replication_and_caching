# Cache-Aside: проблемы и решения

# ❌ Плохо: все лезут в БД одновременно
if not cache.get(key):
    data = expensive_db_query()  # 100 потоков тут!
    cache.set(key, data)

# ✅ Хорошо: распределённая блокировка
lock = cache.set(f"lock:{key}", "1", nx=True, ex=5)
if lock:
    data = expensive_db_query()
    cache.set(key, data)
    cache.delete(f"lock:{key}")
else:
    # Ждём пока другой поток загрузит
    for _ in range(50):
        data = cache.get(key)
        if data: return data
        time.sleep(0.1)
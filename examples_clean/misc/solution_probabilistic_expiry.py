# Решение: Probabilistic Expiry

# ✅ Вероятностное обновление до истечения
def get_with_probabilistic_expiry(key, ttl=300):
    value, expiry = cache.get_with_expiry(key)

    if value is None:
        return fetch_and_cache(key, ttl)

    # Время до истечения
    remaining = expiry - time.time()

    # Вероятность обновления растёт к концу TTL
    beta = 1.0  # Настраиваемый параметр
    xfetch = remaining * math.log(random.random()) * beta

    # Обновляем заранее с некоторой вероятностью
    if xfetch < 0:
        asyncio.create_task(
            refresh_cache_async(key, ttl)
        )

    return value
# Решение 3: Background Refresh

def get_with_refresh(key, ttl, generate_fn):
    value, expiry_time = cache.get_with_expiry(key)

    # Осталось меньше 20% времени? Обновляем!
    if expiry_time - time.now() < ttl * 0.2:
        # Запускаем фоновое обновление
        async_task.delay(
            lambda: cache.set(key, generate_fn(), ttl)
        )

    return value  # Отдаём старое значение сразу
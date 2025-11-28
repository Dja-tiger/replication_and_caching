# Решение 4: Stale-While-Revalidate

def get_stale_while_revalidate(key, ttl, stale_ttl, generate_fn):
    value = cache.get(key)
    age = cache.age(key)  # Как давно в кэше

    if value is None:
        # Кэш пуст - ждём загрузки
        return generate_fn()

    if age < ttl:
        # Данные свежие
        return value
    elif age < stale_ttl:
        # Данные устарели, но ещё годны
        async_task.delay(
            lambda: cache.set(key, generate_fn(), ttl)
        )
        return value  # Отдаём старые
    else:
        # Слишком старые - обновляем синхронно
        return generate_fn()
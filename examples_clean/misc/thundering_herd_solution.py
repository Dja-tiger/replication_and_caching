# Thundering Herd: решение

def get_with_jitter(key, ttl, generate_fn):
    value = cache.get(key)
    remaining_ttl = cache.ttl(key)

    # За 30 секунд до истечения начинаем обновлять
    if remaining_ttl < 30:
        if random.random() < 0.1:  # 10% шанс
            new_value = generate_fn()
            cache.setex(key, ttl, new_value)

    return value
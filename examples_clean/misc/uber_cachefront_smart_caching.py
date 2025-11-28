# Uber CacheFront: умное кэширование

def smart_cache_key(user_id, request_type):
    # Адаптивный TTL на основе частоты
    frequency = get_access_frequency(user_id)
    ttl = calculate_adaptive_ttl(frequency)

    # Приоритетное кэширование
    if is_vip_user(user_id):
        ttl *= 2  # Удвоенное время для VIP

    return cache.set(key, value, ttl)
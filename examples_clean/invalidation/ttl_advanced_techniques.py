# TTL: продвинутые техники

# Адаптивный TTL на основе популярности
class AdaptiveTTL:
    def set_with_adaptive_ttl(self, key, value, access_count):
        """TTL зависит от частоты обращений"""
        if access_count > 1000:
            ttl = 60      # 1 минута для горячих данных
        elif access_count > 100:
            ttl = 600     # 10 минут для теплых
        else:
            ttl = 3600    # 1 час для холодных

        redis.setex(key, ttl, value)

# Скользящий TTL (Sliding TTL)
def get_with_sliding_ttl(key):
    """Продлеваем TTL при каждом обращении"""
    value = redis.get(key)
    if value:
        redis.expire(key, 300)  # Продлеваем на 5 минут
    return value

# TTL с jitter для предотвращения thundering herd
import random
ttl = 300 + random.randint(-30, 30)  # 5 минут ± 30 секунд
redis.setex(key, ttl, value)
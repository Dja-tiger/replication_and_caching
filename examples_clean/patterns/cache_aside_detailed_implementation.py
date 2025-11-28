# Cache-Aside: детальная реализация

# Техномир: полноценная реализация Cache-Aside
class CacheAsidePattern:
    def __init__(self, cache, db, ttl=300):
        self.cache = cache
        self.db = db
        self.ttl = ttl
        self.stats = {"hits": 0, "misses": 0}

    def get(self, key, loader_func):
        """Универсальный метод с lazy loading"""
        # 1. Пытаемся получить из кэша
        cached = self.cache.get(key)
        if cached is not None:
            self.stats["hits"] += 1
            return self._deserialize(cached)

        # 2. Cache miss - загружаем данные
        self.stats["misses"] += 1
        data = loader_func()

        # 3. Сохраняем в кэш на будущее
        if data is not None:
            self.cache.setex(key, self.ttl,
                           self._serialize(data))

        return data
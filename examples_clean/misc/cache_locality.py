# 5. Cache Locality

# Техномир: многоуровневое кэширование
class MultiLevelCache:
    def __init__(self):
        # L1: Process memory (microseconds)
        self.local_cache = LRUCache(maxsize=1000)
        # L2: Redis local (milliseconds)
        self.redis_local = Redis('localhost')
        # L3: Redis remote (10ms)
        self.redis_remote = Redis('cache.technomir.ru')

    def get(self, key):
        # Проверяем от быстрого к медленному
        value = self.local_cache.get(key)
        if value:
            return value

        value = self.redis_local.get(key)
        if value:
            self.local_cache[key] = value
            return value

        value = self.redis_remote.get(key)
        if value:
            self.propagate_down(key, value)
        return value
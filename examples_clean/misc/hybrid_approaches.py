# Гибридные подходы

# Техномир: адаптивный выбор стратегии
class AdaptiveCacheStrategy:
    def __init__(self, cache, db):
        self.cache = cache
        self.db = db
        self.stats = defaultdict(lambda: {
            "reads": 0, "writes": 0, "pattern": "cache-aside"
        })

    def access(self, key, operation, value=None):
        """Автоматический выбор паттерна"""
        stats = self.stats[key]

        if operation == "read":
            stats["reads"] += 1
            pattern = self._choose_read_pattern(stats)
        else:
            stats["writes"] += 1
            pattern = self._choose_write_pattern(stats)

        # Применяем выбранный паттерн
        if pattern == "write-through":
            return self._write_through(key, value)
        elif pattern == "read-through":
            return self._read_through(key)
        else:
            return self._cache_aside(key, value)

    def _choose_read_pattern(self, stats):
        read_ratio = stats["reads"] / (stats["writes"] + 1)
        return "read-through" if read_ratio > 10 else "cache-aside"
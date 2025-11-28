# Мониторинг инвалидации

# Техномир: метрики инвалидации
class InvalidationMetrics:
    def track_invalidation(self, keys, reason):
        # Счетчики по типам
        metrics.increment(f"cache.invalidation.{reason}")
        metrics.increment("cache.invalidation.total", len(keys))

        # Топ самых часто инвалидируемых ключей
        for key in keys:
            key_pattern = self.extract_pattern(key)
            metrics.increment(f"cache.invalidation.pattern.{key_pattern}")
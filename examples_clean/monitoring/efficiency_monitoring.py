# 2. Мониторинг эффективности

# Техномир: метрики кэширования
class CacheMetrics:
    def track_operation(self, operation, key, hit=None):
        # Prometheus метрики
        if operation == 'get':
            cache_requests.labels(key_type=self.get_type(key)).inc()
            if hit:
                cache_hits.labels(key_type=self.get_type(key)).inc()
        elif operation == 'set':
            cache_writes.labels(key_type=self.get_type(key)).inc()

        # Логирование медленных операций
        if duration > 100:  # ms
            logger.warning(f"Slow cache op: {operation} {key} {duration}ms")
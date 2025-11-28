# 3. Graceful Degradation

# ✅ Работа при недоступности кэша
class ResilientCache:
    def get(self, key, fallback=None):
        try:
            return self.redis.get(key)
        except (ConnectionError, TimeoutError):
            # Метрика деградации
            cache_failures.inc()

            # Circuit breaker
            if self.failure_count > 10:
                self.circuit_open = True
                self.reopen_at = time.time() + 30

            # Возврат из БД или stale кэша
            if fallback:
                return fallback()
            return self.get_stale_cache(key)
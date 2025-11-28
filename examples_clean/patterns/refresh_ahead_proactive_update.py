# Refresh-Ahead: проактивное обновление

# Техномир: обновление до истечения TTL
class RefreshAheadCache:
    def __init__(self, cache, db, refresh_threshold=0.8):
        self.cache = cache
        self.db = db
        self.refresh_threshold = refresh_threshold

    def get(self, key):
        """Чтение с упреждающим обновлением"""
        cached = self.cache.get(key)
        ttl = self.cache.ttl(key)
        max_ttl = 300  # 5 минут

        # Проверяем, нужно ли обновить
        if cached and ttl < (max_ttl * (1 - self.refresh_threshold)):
            # Асинхронно обновляем
            threading.Thread(
                target=self._refresh,
                args=(key,)
            ).start()

        # Возвращаем текущее значение сразу
        if cached:
            return cached

        # Cache miss - загружаем синхронно
        return self._load_and_cache(key)

    def _refresh(self, key):
        """Фоновое обновление"""
        fresh_data = self.db.get(key)
        self.cache.setex(key, 300, fresh_data)
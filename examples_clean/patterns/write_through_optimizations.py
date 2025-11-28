# Write-Through: оптимизации

# Техномир: батчинг для Write-Through
class BatchedWriteThrough:
    def __init__(self, cache, db, batch_size=100):
        self.cache = cache
        self.db = db
        self.batch_size = batch_size
        self.buffer = []
        self.lock = threading.Lock()

    def write(self, key, value):
        """Буферизированная запись"""
        with self.lock:
            self.buffer.append((key, value))

            if len(self.buffer) >= self.batch_size:
                self._flush()

    def _flush(self):
        """Сброс батча в БД и кэш"""
        if not self.buffer:
            return

        batch = self.buffer.copy()
        self.buffer.clear()

        # Пишем батчом в БД
        self.db.bulk_upsert(batch)

        # Пишем в кэш pipeline
        pipe = self.cache.pipeline()
        for key, value in batch:
            pipe.set(key, value)
        pipe.execute()
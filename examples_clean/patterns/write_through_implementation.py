# Write-Through: реализация

# Техномир: синхронная запись в кэш и БД
class WriteThroughCache:
    def __init__(self, cache, db):
        self.cache = cache
        self.db = db
        self.write_locks = {}

    def write(self, key, value):
        """Атомарная запись в кэш и БД"""
        lock_key = f"write_lock:{key}"

        # Захватываем блокировку
        with self.cache.lock(lock_key, timeout=5):
            try:
                # 1. Начинаем транзакцию БД
                with self.db.transaction() as tx:
                    # 2. Пишем в БД
                    tx.upsert(key, value)

                    # 3. Пишем в кэш (до коммита!)
                    self.cache.set(key, value)

                    # 4. Коммитим транзакцию
                    tx.commit()

            except Exception as e:
                # Откатываем и кэш тоже
                self.cache.delete(key)
                raise
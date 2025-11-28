# Отложенная и батч-инвалидация

# Техномир: оптимизация частых изменений
class BatchInvalidation:
    def __init__(self):
        self.pending_keys = set()
        self.batch_timer = Timer(1.0, self.flush_batch)  # 1 секунда

    def mark_for_invalidation(self, key):
        """Помечаем ключ для отложенного удаления"""
        self.pending_keys.add(key)
        # Перезапускаем таймер
        self.batch_timer.cancel()
        self.batch_timer = Timer(1.0, self.flush_batch)
        self.batch_timer.start()
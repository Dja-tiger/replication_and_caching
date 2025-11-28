# Комбинированная стратегия: инвалидация

def invalidate(self, trigger_type, trigger_data):
        if trigger_type == "ttl_expired":
            # TTL сам удалит
            pass
        elif trigger_type == "event":
            # Инвалидация по событию
            self.invalidate_by_event(trigger_data)
        elif trigger_type == "tag":
            # Инвалидация по тегу
            cache.delete_by_tag(trigger_data)

# Пример использования
cache.save_to_cache(
    "product:123", product_data,
    context={
        "category": "electronics",
        "importance": "high",
        "update_frequency": "medium"
    }
)
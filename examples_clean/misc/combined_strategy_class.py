# Комбинированная стратегия: класс

class HybridInvalidation:
    """Комбинируем все три подхода"""

    def save_to_cache(self, key, value, context):
        # 1. TTL как базовая защита
        ttl = self.calculate_ttl(context)

        # 2. Теги для групповой инвалидации
        tags = self.extract_tags(context)

        # 3. Подписка на события
        self.subscribe_to_events(key, context)

        # Сохраняем со всеми стратегиями
        cache.set_with_tags(key, value, tags, ttl)
# Использование локальности в архитектуре

# Техномир: многоуровневый кэш с учётом локальности
class LocalityAwareCache:
    def __init__(self):
        # L1: Горячие данные (высокая временная локальность)
        self.hot_cache = LRUCache(capacity=1000)  # 1K самых популярных

        # L2: Тёплые данные (средняя локальность)
        self.warm_cache = LFUCache(capacity=10000)  # 10K часто используемых

        # L3: Холодные данные (низкая локальность)
        self.cold_cache = RedisCache()  # Всё остальное

    def get(self, key):
        # Проверяем уровни по порядку
        value = self.hot_cache.get(key)
        if value:
            return value

        value = self.warm_cache.get(key)
        if value:
            # Продвигаем в горячий кэш при повторном доступе
            self.hot_cache.set(key, value)
            return value

        value = self.cold_cache.get(key)
        if value:
            self.warm_cache.set(key, value)
            return value
# Read-Through: реализация

# Техномир: умный Read-Through кэш
class ReadThroughCache:
    def __init__(self, cache, loaders, ttl=300):
        """
        loaders - словарь функций загрузки по типам
        """
        self.cache = cache
        self.loaders = loaders
        self.ttl = ttl

    def get(self, key):
        """Прозрачное чтение через кэш"""
        # 1. Проверяем кэш
        cached = self.cache.get(key)
        if cached:
            return cached

        # 2. Определяем тип данных по ключу
        data_type = self._extract_type(key)
        loader = self.loaders.get(data_type)

        if not loader:
            raise ValueError(f"No loader for {data_type}")

        # 3. Загружаем данные
        data = loader(key)

        # 4. Кэшируем с умным TTL
        ttl = self._calculate_ttl(data_type, data)
        self.cache.setex(key, ttl, data)

        return data
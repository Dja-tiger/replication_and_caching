# Когда кэш вреден: overhead больше пользы

# Техномир: расчёт накладных расходов
class CacheOverhead:
    def calculate_total_cost(self, request):
        """Полная стоимость обслуживания запроса с кэшем"""
        cache_lookup_ms = 1      # Проверка кэша
        serialize_ms = 5         # Сериализация объекта
        network_ms = 2           # Передача по сети
        deserialize_ms = 3       # Десериализация
        db_query_ms = 15         # Запрос к БД при miss

        cache_hit_cost = cache_lookup_ms + deserialize_ms
        cache_miss_cost = (cache_lookup_ms + db_query_ms +
                          serialize_ms + network_ms)

        # Если hit rate < 60%, то кэш медленнее прямого обращения к БД
        return cache_hit_cost, cache_miss_cost

# БД быстрая (SSD, индексы) + низкий hit rate = кэш вреден
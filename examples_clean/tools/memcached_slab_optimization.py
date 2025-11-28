# Memcached: оптимизация slabs

# Рекомендации по оптимизации для Техномира
def optimize_slab_classes(traffic_pattern):
    if traffic_pattern == "small_objects":
        # Много мелких объектов (сессии)
        return "-f 1.25 -n 48"  # Мелкий шаг роста

    elif traffic_pattern == "mixed":
        # Смешанная нагрузка
        return "-f 1.5 -n 96"  # Стандартные настройки

    elif traffic_pattern == "large_objects":
        # Крупные объекты (кэш страниц)
        return "-f 2.0 -n 256 -I 5m"  # Крупный шаг

# Техномир использует mixed паттерн
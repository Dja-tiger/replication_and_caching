# Антипаттерн: Cache Everything

# ❌ Кэширование ВСЕГО подряд
def get_anything(key):
    cached = cache.get(key)
    if not cached:
        # Кэшируем даже уникальные запросы!
        result = compute_something(key)
        cache.set(key, result)  # Засоряем память
    return cached

# Проблемы:
# - Низкий hit rate (< 10%)
# - Быстрое заполнение памяти
# - Вытеснение полезных данных
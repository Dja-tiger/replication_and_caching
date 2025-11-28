# Антипаттерн: Negative Caching

# ❌ Не кэшируем отсутствующие данные
def get_product(id):
    product = cache.get(f"product:{id}")
    if product:
        return product

    product = db.get_product(id)
    if product:
        cache.set(f"product:{id}", product)
    # Если товара нет - НЕ кэшируем!
    return product

# Проблема: при каждом запросе несуществующего
# товара идём в БД (cache penetration)
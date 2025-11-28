# Проблема: Cache Inconsistency

# ❌ Race condition при обновлении
def bad_update_product(id, price):
    # 1. Клиент А читает товар (цена=100)
    product = db.get_product(id)

    # 2. Клиент B обновляет цену на 120
    # 3. Клиент B обновляет кэш

    # 4. Клиент A обновляет цену на 110
    product.price = price
    db.save(product)

    # 5. Клиент A перезаписывает кэш старой версией!
    cache.set(f"product:{id}", product)
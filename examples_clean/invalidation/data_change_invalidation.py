# Инвалидация при изменении данных

def update_product(product_id, changes):
    # 1. Обновляем БД
    db.update_product(product_id, changes)

    # 2. Инвалидируем прямые кэши
    cache.delete(f"product:{product_id}")
    cache.delete(f"product:{product_id}:details")

    # 3. Инвалидируем связанные кэши
    if 'price' in changes:
        cache.delete(f"category:{product.category_id}:products")
        cache.delete("products:on_sale")

    if 'availability' in changes:
        cache.delete(f"search:category:{product.category_id}")
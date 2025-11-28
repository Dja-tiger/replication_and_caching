# Проблема: Cascading Invalidation

# Техномир: изменение категории влияет на много кэшей
def update_category(category_id, data):
    # Обновляем категорию
    db.update_category(category_id, data)

    # ❌ Нужно инвалидировать ВСЕ связанные кэши
    cache.delete(f"category:{category_id}")

    # Все товары категории (может быть тысячи!)
    products = db.get_products_by_category(category_id)
    for product in products:
        cache.delete(f"product:{product.id}")
        cache.delete(f"product_list:{product.id}")

    # Все страницы с этой категорией
    for page in range(1, 100):
        cache.delete(f"catalog:page:{page}")
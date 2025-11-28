# 2. Инвалидация по событию: детали

# При обновлении товара
def update_product(product_id, changes):
    # 1. Обновляем БД
    db.update_product(product_id, changes)

    # 2. Инвалидируем все связанные кэши
    redis.delete(f"product:{product_id}")
    redis.delete(f"product:{product_id}:details")
    redis.delete(f"category:{product.category_id}")

    # 3. Публикуем событие для других сервисов
    redis.publish("product_updated", product_id)
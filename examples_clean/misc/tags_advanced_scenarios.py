# Теги: продвинутые сценарии

# Множественные теги для одного объекта
cache.set_with_tags(
    "product:123",
    product_data,
    tags=[
        "category:electronics",  # По категории
        "brand:samsung",        # По бренду
        "price:1000-5000",      # По ценовому диапазону
        "user:456",             # Кто последний редактировал
        "featured",             # Рекомендованный товар
        "sale"                  # Участвует в распродаже
    ]
)

# Инвалидация по разным критериям
cache.delete_by_tag("brand:samsung")     # Все товары Samsung
cache.delete_by_tag("sale")              # Все товары на распродаже
cache.delete_by_tag("price:1000-5000")   # Ценовой диапазон

# Пересечение тегов (товары Samsung на распродаже)
def delete_by_tags_intersection(tags):
    sets = [f"tag:{tag}" for tag in tags]
    keys = redis.sinter(*sets)  # Пересечение множеств
    if keys:
        redis.delete(*keys)

delete_by_tags_intersection(["brand:samsung", "sale"])
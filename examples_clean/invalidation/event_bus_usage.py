# События: использование Event Bus

# Использование
bus = CacheEventBus(redis)

@bus.on_entity_changed("product")
def invalidate_product_caches(product_id):
    redis.delete(f"product:{product_id}")
    redis.delete(f"recommendations:{product_id}")

@bus.on_entity_changed("product")
def invalidate_category_cache(product_id):
    product = db.get_product(product_id)
    redis.delete(f"category:{product.category_id}")

# При изменении товара
bus.emit("product", 123)  # Все кэши очистятся
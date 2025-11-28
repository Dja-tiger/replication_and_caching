# Техномир: версионирование кэша

# ✅ Решение с версиями
def safe_update_product(id, updates):
    with db.transaction():
        # Увеличиваем версию атомарно
        db.execute("""
            UPDATE products
            SET price = ?, version = version + 1
            WHERE id = ?
        """, updates['price'], id)

        # Получаем новую версию
        product = db.get_product(id)

        # Кэшируем с версией в ключе
        cache.set(f"product:{id}:v{product.version}",
                 product)
        # Удаляем старые версии
        cache.delete(f"product:{id}:v{product.version-1}")
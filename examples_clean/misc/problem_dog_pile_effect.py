# Проблема: Dog Pile Effect

# ❌ Все клиенты одновременно обновляют кэш
def get_popular_product(product_id):
    product = cache.get(f"product:{product_id}")

    if not product:
        # 1000 запросов одновременно!
        product = expensive_db_query(product_id)
        cache.set(f"product:{product_id}", product)

    return product
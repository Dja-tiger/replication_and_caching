# Cache Warming стратегия Техномир

# Прогрев кэша при старте
def warm_cache_on_startup():
    queries = [
        # ТОП-100 товаров
        "SELECT * FROM products WHERE id IN (
            SELECT product_id FROM orders_items
            GROUP BY product_id ORDER BY COUNT(*) DESC
            LIMIT 100)",

        # Активные акции
        "SELECT * FROM promotions WHERE active = true",

        # Популярные категории
        "SELECT * FROM categories WHERE featured = true"
    ]

    for query in queries:
        results = db.execute(query)
        for item in results:
            cache_key = f"{item.table}:{item.id}"
            redis.setex(cache_key, 3600, item.to_json())
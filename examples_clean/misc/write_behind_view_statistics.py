# Write-Behind: статистика просмотров

def track_product_view(product_id, user_id):
    # Быстро пишем в кэш
    redis.hincrby(f"views:{product_id}", "total", 1)
    redis.lpush(f"view_queue", json.dumps({
        "product_id": product_id,
        "user_id": user_id,
        "timestamp": time.time()
    }))

    # Batch worker (каждые 30 сек)
    def flush_views():
        batch = redis.lrange("view_queue", 0, 1000)
        if batch:
            db.bulk_insert("product_views", batch)
            redis.ltrim("view_queue", 1001, -1)
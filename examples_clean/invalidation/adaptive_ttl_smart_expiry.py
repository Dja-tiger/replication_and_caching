# Adaptive TTL: умное время жизни

# Техномир: адаптивный TTL на основе популярности
def calculate_ttl(product_id):
    views = redis.get(f"views:{product_id}")
    base_ttl = 300  # 5 минут базовый

    if views > 1000:
        return base_ttl * 4  # 20 минут для хитов
    elif views > 100:
        return base_ttl * 2  # 10 минут
    else:
        return base_ttl      # 5 минут

def cache_product(product_id, data):
    ttl = calculate_ttl(product_id)
    redis.setex(f"product:{product_id}",
                ttl, json.dumps(data))
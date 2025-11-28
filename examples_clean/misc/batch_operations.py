# 6. Batch Operations

# ❌ N операций - N round trips
for product_id in product_ids:
    product = cache.get(f"product:{product_id}")
    products.append(product)

# ✅ 1 операция - 1 round trip
keys = [f"product:{id}" for id in product_ids]
products = cache.mget(keys)

# Pipeline для множественных операций
pipe = redis.pipeline()
for id in product_ids:
    pipe.get(f"product:{id}")
    pipe.get(f"inventory:{id}")
results = pipe.execute()  # Одна команда!
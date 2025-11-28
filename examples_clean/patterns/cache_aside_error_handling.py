# Cache-Aside: обработка ошибок

# Техномир: graceful degradation при сбое кэша
def get_product_safe(product_id):
    try:
        # Пытаемся использовать кэш
        product = cache_aside.get(
            f"product:{product_id}",
            lambda: db.get_product(product_id)
        )
    except RedisError as e:
        # Кэш недоступен - работаем напрямую с БД
        logger.warning(f"Cache unavailable: {e}")
        product = db.get_product(product_id)

        # Увеличиваем TTL в БД-соединении
        db.set_cache_hint(True)

    except DatabaseError as e:
        # БД недоступна - пытаемся stale кэш
        stale = cache.get(f"product:{product_id}:stale")
        if stale:
            logger.warning("Serving stale data")
            return {"data": stale, "stale": True}
        raise

    return product
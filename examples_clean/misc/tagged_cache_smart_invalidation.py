# Тегированный кэш для умной инвалидации

# Сохраняем с тегами
cache.set_with_tags("post:123", post_data,
    tags=["user:vasia", "category:blog", "type:best"])

cache.set_with_tags("sidebar:best", sidebar_data,
    tags=["type:best", "sidebar"])

cache.set_with_tags("feed:main", feed_data,
    tags=["category:blog", "feed"])

# Инвалидация по тегу - удалит ВСЕ связанное
cache.delete_by_tag("type:best")  # Удалит post:123 и sidebar:best
cache.delete_by_tag("user:vasia")  # Удалит все посты Васи
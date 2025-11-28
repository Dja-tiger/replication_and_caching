# TTL стратегии по типам данных

# Критично для бизнеса - короткий TTL
cache.setex("sidebar:best", 600, best_posts)  # 10 мин

# Редко меняется - длинный TTL
cache.setex("categories:nav", 43200, categories)  # 12 часов

# Персистентные данные - без TTL
cache.set("post:featured", featured_post)  # Навсегда

# Статистика - средний TTL
cache.setex("stats:section", 3600, stats)  # 1 час
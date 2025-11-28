# 1. Правильный выбор ключей

# ❌ Плохо: нестабильные ключи
cache_key = f"user_{timestamp}_{random_id}"

# ✅ Хорошо: предсказуемые и читаемые
cache_key = f"user:{user_id}:profile:v{version}"
cache_key = f"product:{id}:lang:{lang}:cur:{currency}"

# Техномир: иерархические ключи
cache_keys = {
    "catalog:category:15:page:1:sort:price",
    "product:12345:full",
    "product:12345:brief",
    "cart:user:9876:items",
    "recommendations:user:9876:home"
}
# Тегированный кэш (Tag) на сайте

cache.set_with_tags(
    f"recommendations:{user_id}",
    recommendations_data,
    tags=[
        f"user:{user_id}",      # Привязка к пользователю
        "type:recommended",     # Тип блока
        "ml:model_v2",         # Версия ML модели
        "category:*"           # Связь с категориями
    ],
    ttl=3600  # + TTL для страховки
)

# Обновление ML модели - очистка всех рекомендаций
cache.delete_by_tag("ml:model_v2")
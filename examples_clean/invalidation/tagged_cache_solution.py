# Решение: Tagged Cache

# ✅ Инвалидация по тегам
class TaggedCache:
    def set_with_tags(self, key, value, tags):
        # Сохраняем значение
        self.cache.set(key, value)

        # Связываем с тегами
        for tag in tags:
            self.cache.sadd(f"tag:{tag}", key)

    def invalidate_by_tag(self, tag):
        # Получаем все ключи с тегом
        keys = self.cache.smembers(f"tag:{tag}")

        # Удаляем их одной командой
        if keys:
            self.cache.delete(*keys)
        self.cache.delete(f"tag:{tag}")

# Использование в Техномире
cache.set_with_tags(f"product:{id}", product,
    tags=[f"category:{cat_id}", f"brand:{brand_id}"])
cache.invalidate_by_tag(f"category:{cat_id}")  # Всё сразу!
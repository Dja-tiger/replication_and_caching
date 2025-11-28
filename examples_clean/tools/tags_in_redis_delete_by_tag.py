# Теги в Redis: удаление по тегу

def delete_by_tag(self, tag):
        """Удаляем все ключи с тегом"""
        # 1. Получаем все ключи с этим тегом
        keys = self.redis.smembers(f"tag:{tag}")

        # 2. Удаляем все ключи
        if keys:
            self.redis.delete(*keys)

        # 3. Удаляем сам тег
        self.redis.delete(f"tag:{tag}")

        return len(keys) if keys else 0
# Теги в Redis: реализация

class TaggedCache:
    def __init__(self, redis):
        self.redis = redis

    def set_with_tags(self, key, value, tags, ttl=None):
        """Сохраняем с тегами"""
        # 1. Сохраняем само значение
        if ttl:
            self.redis.setex(key, ttl, value)
        else:
            self.redis.set(key, value)

        # 2. Добавляем ключ в каждый тег (через Set)
        for tag in tags:
            self.redis.sadd(f"tag:{tag}", key)
            # TTL для тега = максимальный TTL всех ключей
            if ttl:
                self.redis.expire(f"tag:{tag}", ttl)
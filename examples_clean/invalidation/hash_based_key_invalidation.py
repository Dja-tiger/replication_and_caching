# Инвалидация по хешированным ключам

# Техномир: инвалидация через hash tags
class HashTagInvalidation:
    def cache_product_data(self, product_id, category_id):
        # Используем hash tag для группировки
        key = f"product:{{{category_id}}}:{product_id}"
        cache.set(key, data, ttl=3600)

    def invalidate_category(self, category_id):
        # Удаляем все ключи категории одной командой
        # В Redis Cluster ключи с одинаковым hash tag
        # попадут на один шард
        pattern = f"*{{{category_id}}}*"
        self.safe_delete_pattern(pattern)

# Преимущество: эффективная групповая инвалидация
# Недостаток: неравномерное распределение по шардам
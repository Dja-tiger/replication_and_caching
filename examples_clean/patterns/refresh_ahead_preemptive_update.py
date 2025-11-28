# Refresh-Ahead: упреждающее обновление

# Техномир: обновление популярных товаров
class RefreshAheadCache:
    def get_product(self, product_id):
        product = redis.get(f"product:{product_id}")
        ttl = redis.ttl(f"product:{product_id}")

        # Обновляем заранее до истечения
        if ttl < 60:  # Осталось меньше минуты
            self.schedule_refresh(product_id)

        return product

    def schedule_refresh(self, product_id):
        # Асинхронное обновление
        celery.send_task('refresh_product',
                         args=[product_id])
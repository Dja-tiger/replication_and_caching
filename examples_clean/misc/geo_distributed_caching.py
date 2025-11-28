# Геораспределённое кэширование

# Техномир: кэш для разных регионов
class GeoDistributedCache:
    def __init__(self):
        self.regions = {
            'moscow': Redis('cache-msk.technomir.ru'),
            'spb': Redis('cache-spb.technomir.ru'),
            'ekb': Redis('cache-ekb.technomir.ru')
        }

    def get_nearest_cache(self, user_ip):
        region = geoip.get_region(user_ip)
        return self.regions.get(region,
                                self.regions['moscow'])

    def replicate_hot_data(self):
        # Репликация популярных товаров
        for product_id in self.get_hot_products():
            data = self.regions['moscow'].get(product_id)
            for cache in self.regions.values():
                cache.set(product_id, data)
# Пространственная локальность в кэше

# Техномир: предзагрузка связанных товаров
class SpatialPrefetcher:
    def __init__(self, cache, db):
        self.cache = cache
        self.db = db

    def get_product_with_prefetch(self, product_id):
        # 1. Получаем основной товар
        product = self.cache.get(f"product:{product_id}")
        if not product:
            product = self.db.get_product(product_id)
            self.cache.set(f"product:{product_id}", product)

        # 2. Предзагружаем связанные товары (spatial locality)
        self.prefetch_related(product)

        return product

    def prefetch_related(self, product):
        """Асинхронная предзагрузка связанных данных"""
        # Товары той же категории
        category_products = self.db.get_category_products(
            product.category_id, limit=10
        )
        for p in category_products:
            self.cache.set(f"product:{p.id}", p, ttl=300)
# Когда кэш бесполезен: равномерное распределение

# Антипаттерн: равномерный доступ ко всем данным
class UniformAccess:
    def simulate_requests(self, num_products=1000000):
        """Имитация равномерного доступа"""
        requests = []
        for i in range(10000):  # 10K запросов
            # Случайный товар из миллиона
            product_id = random.randint(1, num_products)
            requests.append(f"product:{product_id}")

        # Результат: почти все запросы уникальны
        # Hit rate ≈ 1% → кэш бесполезен
        return requests

# Техномир: реальное распределение следует закону Парето
# 20% товаров генерируют 80% запросов → кэш эффективен
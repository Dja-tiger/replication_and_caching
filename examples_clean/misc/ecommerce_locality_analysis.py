# Техномир: анализ локальности

class LocalityAnalyzer:
    def analyze_access_pattern(self, access_log):
        """Анализ паттернов доступа к товарам"""

        # Временная локальность: 80/20 правило Парето
        total_requests = len(access_log)
        unique_products = set(access_log)

        # Топ 20% товаров
        product_counts = Counter(access_log)
        top_20_percent = int(len(unique_products) * 0.2)
        top_products = product_counts.most_common(top_20_percent)

        # Сколько запросов они обслуживают?
        top_requests = sum(count for _, count in top_products)
        coverage = top_requests / total_requests

        # Техномир: 20% товаров = 78% запросов
        return {
            "temporal_locality": coverage,
            "hot_products": [id for id, _ in top_products],
            "cache_size_recommendation": top_20_percent
        }
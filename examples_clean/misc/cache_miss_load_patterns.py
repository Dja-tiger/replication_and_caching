# Cache Miss: характер нагрузки

# Техномир: анализ паттернов доступа
class CacheAnalyzer:
    def analyze_access_pattern(self, requests):
        """Определяем, поможет ли кэширование"""
        unique_keys = set()
        repeated_keys = 0

        for request in requests:
            if request.key in unique_keys:
                repeated_keys += 1
            unique_keys.add(request.key)

        repeat_ratio = repeated_keys / len(requests)

        if repeat_ratio < 0.1:  # < 10% повторов
            return "ПЛОХО для кэширования"
        elif repeat_ratio > 0.8:  # > 80% повторов
            return "ОТЛИЧНО для кэширования"
        else:
            return "СРЕДНЕ для кэширования"
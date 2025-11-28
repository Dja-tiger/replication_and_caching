# Метрики локальности

# Техномир: измерение эффективности локальности
class LocalityMetrics:
    def calculate_metrics(self, access_log, cache_state):
        """Расчёт метрик локальности кэша"""

        # 1. Temporal locality score
        reuse_distance = []
        last_access = {}
        for i, item in enumerate(access_log):
            if item in last_access:
                reuse_distance.append(i - last_access[item])
            last_access[item] = i

        avg_reuse_distance = np.mean(reuse_distance)
        temporal_score = 1 / (1 + avg_reuse_distance)

        # 2. Spatial locality score
        sequential_hits = 0
        for i in range(1, len(access_log)):
            if abs(access_log[i] - access_log[i-1]) <= 10:
                sequential_hits += 1

        spatial_score = sequential_hits / len(access_log)

        # 3. Working set size
        working_set = len(set(access_log[-1000:]))  # Последние 1000

        return {
            "temporal_locality": temporal_score,
            "spatial_locality": spatial_score,
            "working_set_size": working_set,
            "cache_efficiency": 1 - (working_set / cache_state.size)
        }
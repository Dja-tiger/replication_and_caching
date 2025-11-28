# Memcached: анализ памяти

# Анализатор использования памяти для Техномира
class MemcachedAnalyzer:
    def analyze_slab_efficiency(self, stats):
        """Анализ эффективности slab allocation"""
        inefficient_slabs = []

        for slab_id, slab_stats in stats['slabs'].items():
            if slab_stats['used_chunks'] > 0:
                efficiency = (slab_stats['used_chunks'] /
                            slab_stats['total_chunks'])
                if efficiency < 0.5:  # Менее 50% использования
                    inefficient_slabs.append({
                        'slab_id': slab_id,
                        'efficiency': efficiency
                    })
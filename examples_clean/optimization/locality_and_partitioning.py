# Локальность и партиционирование

# Техномир: партиционирование с сохранением локальности
class LocalityPreservingPartitioner:
    def partition_by_locality(self, data):
        """Группируем данные для максимальной локальности"""

        # 1. Партиция по пользователям (session affinity)
        user_partitions = {}
        for item in data:
            user_id = item['user_id']
            if user_id not in user_partitions:
                user_partitions[user_id] = []
            user_partitions[user_id].append(item)

        # 2. Партиция по категориям (data affinity)
        category_partitions = {}
        for item in data:
            category = item['category']
            shard = hash(category) % NUM_SHARDS
            if shard not in category_partitions:
                category_partitions[shard] = []
            category_partitions[shard].append(item)

        # 3. Географическая локальность (geo affinity)
        geo_partitions = self.partition_by_region(data)

        return user_partitions, category_partitions, geo_partitions
# Two-tier кэширование

# Техномир: L1 (процесс) + L2 (Redis)
class TwoTierCache:
    def __init__(self):
        self.l1_cache = {}  # In-process
        self.l2_cache = redis.Redis()

    def get(self, key):
        # Проверяем L1 (microseconds)
        if key in self.l1_cache:
            age = time.time() - self.l1_cache[key]['ts']
            if age < 10:  # 10 сек в L1
                return self.l1_cache[key]['data']

        # Проверяем L2 (milliseconds)
        data = self.l2_cache.get(key)
        if data:
            self.l1_cache[key] = {
                'data': data,
                'ts': time.time()
            }
        return data
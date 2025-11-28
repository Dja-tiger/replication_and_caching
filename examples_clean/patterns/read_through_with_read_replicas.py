# Read-Through с Read Replicas

class SmartCache:
    def __init__(self, cache, master, replicas):
        self.cache = cache
        self.master = master
        self.replicas = replicas

    def get(self, key, consistency="eventual"):
        cached = self.cache.get(key)
        if cached:
            return cached

        # Выбираем источник
        if consistency == "strong":
            db = self.master
        else:
            db = self.select_healthy_replica()

        data = db.query(key)
        self.cache.set(key, data, ttl=300)
        return data
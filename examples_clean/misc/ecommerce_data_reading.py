# Техномир: чтение данных

def get_product(self, id, consistency="eventual"):
        # 1. Пробуем кэш
        cached = self.cache.get(f"product:{id}")
        if cached:
            return cached

        # 2. Выбираем БД по consistency
        db = self.master if consistency == "strong" \
             else random.choice(self.replicas)

        # 3. Кэшируем с умным TTL
        product = db.query("SELECT * FROM products...")
        self.cache.set_adaptive(f"product:{id}", product)
        return product
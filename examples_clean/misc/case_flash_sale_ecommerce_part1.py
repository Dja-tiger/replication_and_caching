# Кейс: Flash Sale в Техномире (1/2)

# Подготовка к внезапной нагрузке
class FlashSaleHandler:
    def prepare_flash_sale(self, product_ids):
        # 1. Прогреваем кэш заранее
        for pid in product_ids:
            product = db.query(f"SELECT * FROM products
                                WHERE id = {pid}")
            # Долгий TTL для акции
            redis.setex(f"flash:{pid}", 3600, product)

        # 2. Создаём счётчики остатков
        for pid in product_ids:
            inventory = db.query(f"SELECT quantity...")
            redis.set(f"inventory:{pid}", inventory)
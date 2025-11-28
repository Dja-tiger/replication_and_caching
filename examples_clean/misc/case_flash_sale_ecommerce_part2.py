# Кейс: Flash Sale в Техномире (2/2)

def process_order(self, product_id, user_id):
        # Декрементим в Redis атомарно
        remaining = redis.decr(f"inventory:{product_id}")
        if remaining < 0:
            redis.incr(f"inventory:{product_id}")
            return {"error": "Товар закончился"}

        # Асинхронная запись в БД
        queue.send("order.created", {
            "product_id": product_id,
            "user_id": user_id,
            "timestamp": time.time()
        })
        return {"success": True}
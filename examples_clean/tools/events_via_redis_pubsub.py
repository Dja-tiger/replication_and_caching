# События через Redis Pub/Sub

# Publisher (сервис, меняющий данные)
def publish_change_event(entity_type, entity_id, action):
    event = {
        "type": entity_type,
        "id": entity_id,
        "action": action,  # created, updated, deleted
        "timestamp": time.time()
    }
    redis.publish("cache_invalidation", json.dumps(event))

# Subscriber (сервис кэширования)
def cache_invalidation_subscriber():
    pubsub = redis.pubsub()
    pubsub.subscribe("cache_invalidation")

    for message in pubsub.listen():
        if message["type"] == "message":
            event = json.loads(message["data"])

            # Инвалидируем по типу события
            if event["type"] == "product":
                invalidate_product_caches(event["id"])
            elif event["type"] == "user":
                invalidate_user_caches(event["id"])

# Запускаем в отдельном потоке
threading.Thread(target=cache_invalidation_subscriber).start()
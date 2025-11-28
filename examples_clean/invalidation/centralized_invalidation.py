# Централизованная инвалидация

# Техномир: система событий для инвалидации
class CacheInvalidationService:
    def __init__(self):
        self.event_bus = EventBus()
        self.register_handlers()

    def register_handlers(self):
        self.event_bus.on("product.updated", self.on_product_update)
        self.event_bus.on("category.changed", self.on_category_change)
        self.event_bus.on("price.changed", self.on_price_change)
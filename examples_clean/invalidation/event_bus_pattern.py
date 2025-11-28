# События: Event Bus паттерн

# Паттерн 1: Event Bus
class CacheEventBus:
    def __init__(self, redis):
        self.redis = redis
        self.handlers = defaultdict(list)

    def on_entity_changed(self, entity_type):
        """Декоратор для обработчиков"""
        def decorator(func):
            self.handlers[entity_type].append(func)
            return func
        return decorator

    def emit(self, entity_type, entity_id):
        """Вызываем все обработчики"""
        for handler in self.handlers[entity_type]:
            handler(entity_id)
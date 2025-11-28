# Cache Segmentation: по типам данных

# Техномир: разные TTL для разных данных
CACHE_CONFIGS = {
    'products': {
        'ttl': 300,      # 5 минут для товаров
        'policy': 'lru'
    },
    'prices': {
        'ttl': 60,       # 1 минута для цен
        'policy': 'volatile-lru'
    },
    'inventory': {
        'ttl': 30,       # 30 сек для остатков
        'policy': 'volatile-ttl'
    },
    'static': {
        'ttl': 3600,     # 1 час для категорий
        'policy': 'allkeys-lfu'
    }
}
# 4. Правильные TTL

# Техномир: адаптивные TTL
TTL_CONFIG = {
    # Статичные данные - долгий TTL
    'categories': 3600,      # 1 час
    'brands': 3600,

    # Динамичные - короткий TTL
    'inventory': 30,         # 30 сек
    'prices': 60,           # 1 минута

    # Персональные - средний TTL
    'cart': 300,            # 5 минут
    'recommendations': 600,  # 10 минут

    # Популярные - увеличенный TTL
    'trending': lambda views: 300 * (1 + log(views))
}
# Sentinel в приложении (2/2)

# Техномир: подключение через Sentinel
from redis.sentinel import Sentinel

sentinels = [
    ('sentinel1.redis', 26379),
    ('sentinel2.redis', 26379),
    ('sentinel3.redis', 26379)
]

sentinel = Sentinel(sentinels,
                   password='strongpass')

# Автоматическое обнаружение мастера
master = sentinel.master_for('mymaster',
                            socket_timeout=0.1)

# Чтение с реплик для балансировки
slave = sentinel.slave_for('mymaster',
                          socket_timeout=0.1)

# Использование
master.set('product:123', json.dumps(data))
product = slave.get('product:123')
# Memcached: установка и запуск

# Установка для Техномира
apt install memcached libmemcached-tools

# Конфигурация /etc/memcached.conf
-m 4096          # 4GB памяти
-p 11211         # Порт
-u memcache      # Пользователь
-c 10000         # Макс соединений
-t 8             # Потоки (по числу CPU)
-I 2m            # Макс размер объекта 2MB

# Запуск кластера для Техномира
memcached -d -m 4096 -p 11211 -t 8
memcached -d -m 4096 -p 11212 -t 8
memcached -d -m 4096 -p 11213 -t 8

# Проверка
echo "stats" | nc localhost 11211
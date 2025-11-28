# ТЕХНОМИР - Демо интернет-магазина с кэшированием

Полнофункциональное демо-приложение интернет-магазина с реализацией различных стратегий кэширования и логической репликацией PostgreSQL.

## 🎯 Функциональность

- **TTL кэширование** (1 час) - для бестселлеров и рекомендаций
- **Тегированное кэширование** - для персональных рекомендаций
- **Event-based инвалидация** - для flash sales и профилей пользователей
- **WebSocket** - для real-time уведомлений
- **Корзина покупок** - управление товарами в корзине
- **Управление кэшами** - API для инвалидации различных типов кэшей

## 🏗️ Архитектура

```
[Frontend] -> [Nginx] -> [Go Backend] -> [PostgreSQL]
                    \-> [Redis Cache]
                    \-> [WebSocket Hub]
```

## 🚀 Быстрый запуск

### 1. Клонирование и запуск

```bash
cd examples/ecommerce_demo
docker-compose up -d
```

### 2. Проверка статуса сервисов

```bash
docker-compose ps
```

Все сервисы должны быть в статусе `Up`.

### 3. Доступ к приложению

- **Главная страница**: http://localhost
- **API**: http://localhost/api/
- **pgAdmin**: http://localhost:8002 (admin@demo.com / admin)
- **Redis Insight**: http://localhost:8001
- **Redis Commander**: http://localhost:8003

## 📋 API Endpoints

### Основные данные
```
GET  /api/bestsellers       - Бестселлеры (TTL кэш 1ч)
GET  /api/recommendations   - Рекомендации (тегированный кэш)
GET  /api/flash-sales       - Flash sales (event-based)
GET  /api/user/profile      - Профиль пользователя
PUT  /api/user/profile      - Обновление профиля
GET  /api/comments/top      - Топ комментарии
```

### Корзина
```
GET  /api/cart              - Содержимое корзины
POST /api/cart/add/{id}     - Добавить товар в корзину
```

### Управление кэшами
```
GET  /api/cache/status                    - Статус всех кэшей
POST /api/cache/invalidate/bestsellers    - Инвалидация бестселлеров
POST /api/cache/invalidate/recommendations - Инвалидация рекомендаций
POST /api/cache/invalidate/flash-sales    - Инвалидация flash sales
POST /api/cache/invalidate/profile        - Инвалидация профиля
POST /api/cache/invalidate/all            - Инвалидация всех кэшей
```

### WebSocket
```
WS   /ws                    - WebSocket соединение для real-time
```

## 🧪 Тестирование кэширования

### 1. Проверка TTL кэширования бестселлеров

```bash
# Первый запрос - загрузка из БД
curl http://localhost/api/bestsellers

# Второй запрос - из кэша (быстрее)
curl http://localhost/api/bestsellers

# Проверка статуса кэша
curl http://localhost/api/cache/status
```

### 2. Инвалидация кэша бестселлеров

```bash
# Инвалидируем кэш
curl -X POST http://localhost/api/cache/invalidate/bestsellers

# Проверяем статус - кэш должен исчезнуть
curl http://localhost/api/cache/status
```

### 3. Тестирование тегированного кэша

```bash
# Запрос рекомендаций - создается тегированный кэш
curl http://localhost/api/recommendations

# Инвалидация по тегу
curl -X POST http://localhost/api/cache/invalidate/recommendations
```

### 4. Event-based инвалидация профиля

```bash
# Получение профиля - кэшируется
curl http://localhost/api/user/profile

# Обновление профиля - автоматически инвалидирует кэш
curl -X PUT http://localhost/api/user/profile \
  -H "Content-Type: application/json" \
  -d '{"name": "Новое имя"}'
```

## 🔍 Мониторинг кэша

### Redis Commander (рекомендуется)
1. Откройте http://localhost:8003
2. Изучайте ключи кэша в real-time:
   - `bestsellers` - TTL кэш
   - `recommendations:user:*` - тегированный кэш
   - `flash_sales` - event-based кэш
   - `user_profile:*` - профили пользователей

### Redis Insight (альтернатива)
1. Откройте http://localhost:8001
2. Добавьте соединение: `redis:6379`

## 📊 Структура базы данных

### Таблицы
- `users` - Пользователи
- `products` - Товары
- `comments` - Комментарии к товарам
- `cart_items` - Элементы корзины
- `flash_sales` - Flash распродажи

### Seed данные
При запуске автоматически создаются:
- 3 тестовых пользователя
- 6 товаров (iPhone, MacBook, AirPods, Samsung, PlayStation, Xbox)
- 1 активная flash sale
- 3 комментария к товарам

## 🔄 Настройка логической репликации PostgreSQL

### 1. Создание сети Docker

```bash
docker network create pgnet
```

### 2. Запуск master-узла PostgreSQL

```bash
docker run -d \
  --name pg-master \
  --network pgnet \
  -e POSTGRES_PASSWORD=masterpass \
  -e POSTGRES_DB=ecommerce_db \
  -p 5432:5432 \
  -v postgres_master:/var/lib/postgresql/data \
  postgres:15 \
  -c wal_level=logical \
  -c max_wal_senders=10 \
  -c max_replication_slots=10 \
  -c listen_addresses='*'
```

### 3. Создание пользователя-репликатора и публикации

Подключаемся к `pg-master`:

```bash
docker exec -it pg-master psql -U postgres -d ecommerce_db
```

Выполняем настройку репликации:

```sql
-- Создаём роль для логической репликации
CREATE ROLE replicator WITH LOGIN PASSWORD 'replpass' REPLICATION;

-- Даём доступ к базе и схеме
GRANT CONNECT ON DATABASE ecommerce_db TO replicator;
GRANT USAGE ON SCHEMA public TO replicator;

-- Даём доступ к таблицам
GRANT SELECT ON ALL TABLES IN SCHEMA public TO replicator;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO replicator;

-- Создаём публикации для разных типов данных
CREATE PUBLICATION pub_products FOR TABLE products;
CREATE PUBLICATION pub_users FOR TABLE users;
CREATE PUBLICATION pub_flash_sales FOR TABLE flash_sales;
```

### 4. Запуск реплики

```bash
docker run -d \
  --name pg-replica \
  --network pgnet \
  -e POSTGRES_PASSWORD=replicapass \
  -e POSTGRES_DB=ecommerce_db \
  -p 5433:5432 \
  -v postgres_replica:/var/lib/postgresql/data \
  postgres:15
```

### 5. Настройка доступа (pg_hba.conf)

Редактируем `pg_hba.conf` в `pg-master`:

```bash
docker exec -it pg-master bash
echo "host ecommerce_db replicator 0.0.0.0/0 md5" >> /var/lib/postgresql/data/pg_hba.conf
su postgres
pg_ctl reload
exit
exit
```

### 6. Создание подписки на реплике

Подключаемся к `pg-replica`:

```bash
docker exec -it pg-replica psql -U postgres -d ecommerce_db
```

Создаём таблицы и подписки:

```sql
-- Создаём структуру таблиц (схема должна совпадать с master)
CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255),
  price INTEGER,
  category VARCHAR(100),
  brand VARCHAR(100),
  description TEXT,
  stock INTEGER,
  is_bestseller BOOLEAN DEFAULT FALSE,
  is_flash_sale BOOLEAN DEFAULT FALSE,
  flash_price INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255),
  email VARCHAR(255) UNIQUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE flash_sales (
  id SERIAL PRIMARY KEY,
  product_id INTEGER,
  sale_price INTEGER,
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Создаём подписки
CREATE SUBSCRIPTION sub_products
  CONNECTION 'host=pg-master port=5432 user=replicator password=replpass dbname=ecommerce_db'
  PUBLICATION pub_products;

CREATE SUBSCRIPTION sub_users
  CONNECTION 'host=pg-master port=5432 user=replicator password=replpass dbname=ecommerce_db'
  PUBLICATION pub_users;

CREATE SUBSCRIPTION sub_flash_sales
  CONNECTION 'host=pg-master port=5432 user=replicator password=replpass dbname=ecommerce_db'
  PUBLICATION pub_flash_sales;
```

### 7. Проверка репликации

На `pg-master`:

```sql
docker exec -it pg-master psql -U postgres -d ecommerce_db

-- Добавляем новый товар
INSERT INTO products (name, price, category, brand, description, stock, is_bestseller)
VALUES ('Test Product', 5000, 'test', 'Test Brand', 'Test Description', 100, true);

-- Проверяем flash sales
SELECT * FROM flash_sales;
```

На `pg-replica`:

```sql
docker exec -it pg-replica psql -U postgres -d ecommerce_db

-- Проверяем что данные реплицировались
SELECT * FROM products WHERE name = 'Test Product';
SELECT * FROM users;
SELECT * FROM flash_sales;
```

### 8. Мониторинг репликации

Проверка статуса репликации на master:

```sql
-- Слоты репликации
SELECT * FROM pg_replication_slots;

-- Активные соединения репликации
SELECT * FROM pg_stat_replication;
```

Проверка подписок на replica:

```sql
-- Статус подписок
SELECT * FROM pg_subscription;

-- Статистика репликации
SELECT * FROM pg_stat_subscription;
```

## 🛠️ Полезные команды

### Docker
```bash
# Перезапуск сервисов
docker-compose restart

# Просмотр логов
docker-compose logs -f app

# Остановка и очистка
docker-compose down -v
```

### Подключение к базе данных
```bash
# Основная БД
docker exec -it ecommerce_postgres psql -U demo_user -d ecommerce_db

# Redis CLI
docker exec -it ecommerce_redis redis-cli
```

### Тестирование производительности
```bash
# Нагрузочное тестирование API
ab -n 1000 -c 10 http://localhost/api/bestsellers

# Тестирование с инвалидацией кэша
for i in {1..10}; do
  curl -X POST http://localhost/api/cache/invalidate/bestsellers
  time curl http://localhost/api/bestsellers > /dev/null
  sleep 1
done
```

## 🎓 Образовательные аспекты

Это демо иллюстрирует:

1. **TTL кэширование** - автоматическое истечение через время
2. **Тегированное кэширование** - группировка связанных данных
3. **Event-based инвалидация** - немедленная очистка при изменениях
4. **WebSocket интеграция** - real-time уведомления об изменениях
5. **Логическая репликация** - синхронизация данных между узлами БД

## 🔧 Настройка для разработки

### Изменение конфигурации кэша

В `main.go` можно настроить:

```go
// TTL для бестселлеров (текущее значение: 1 час)
time.Hour

// Изменить на 5 минут для тестирования:
5 * time.Minute
```

### Добавление новых типов кэширования

1. Добавьте новую функцию в `CacheService`
2. Создайте соответствующий handler
3. Зарегистрируйте новый endpoint в роутере

## 📚 Дополнительные ресурсы

- [Redis документация](https://redis.io/documentation)
- [PostgreSQL Logical Replication](https://www.postgresql.org/docs/current/logical-replication.html)
- [Gorilla WebSocket](https://github.com/gorilla/websocket)
- [GORM документация](https://gorm.io/docs/)

---

🎉 **Готово!** Демо полностью функционально и готово для изучения стратегий кэширования и репликации базы данных.
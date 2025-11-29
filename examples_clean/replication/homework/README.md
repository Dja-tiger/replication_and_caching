# Репликация PostgreSQL: практическое ДЗ

Этот пример закрывает требования из задания: развернуть мастер с двумя слейвами, включить потоковую репликацию (асинхронную и кворумную синхронную), перенести два запроса на чтение на слейвы, провести нагрузочные тесты и проверить отсутствие потерь транзакций при аварии мастера.

## Состав окружения

`docker-compose.yml` поднимает 4 сервиса:

- `primary` — основной узел PostgreSQL с включенным `wal_level=replica`, слоты `replica1_slot`/`replica2_slot` и параметром `synchronous_standby_names='FIRST 1 (replica1, replica2)'` для кворумной синхронной репликации.
- `replica1` и `replica2` — горячие standby. При первом старте делают `pg_basebackup` с мастера, подключаются через выделенный слот и включают `hot_standby=on`.
- `pgpool` — простой роутер для чтения. Включен `PGPOOL_ENABLE_LOAD_BALANCING=yes`: все read-only подключения пользователя `readonly` распределяются по `replica1` и `replica2` (round-robin).

Порты:
- `5432` — прямое подключение к мастеру (для записи и административных задач).
- `5433`/`5434` — прямые подключения к каждой реплике (для диагностики).
- `9999` — точка входа Pgpool для распределённого чтения.

## Быстрый старт

```bash
docker compose -f replication/homework/docker-compose.yml up -d
```

PostgreSQL создаёт пользователей и данные в `primary/init/01-setup.sql`:
- репликация: `replicator/replicate_me`
- приложение: `app/app_password` (БД `appdb`)
- read-only: `readonly/readonly_password`

Проверка состояния репликации:
```bash
docker exec -it pg-primary psql -U app -d appdb \
  -c "select client_addr, state, sync_state, sent_lsn, replay_lsn from pg_stat_replication;"
```

## Перенос чтения на слейвы

Типичные запросы из спецификации `/user/get/{id}` и `/user/search` можно обслуживать через Pgpool как read-only пользователя:

- `/user/get/{id}` → `SELECT * FROM users WHERE id = $1;`
- `/user/search`  → `SELECT * FROM users WHERE name ILIKE '%' || $1 || '%' ORDER BY created_at DESC LIMIT 50;`

В приложении достаточно отправлять все запросы только на чтение на `pgpool:9999` под пользователем `readonly`. Запись (`INSERT/UPDATE/DELETE`) остаётся на мастере (`primary:5432`, пользователь `app`).

## Нагрузочное тестирование

### Базовый прогрев данных
```bash
pgbench -i -h localhost -p 5432 -U app appdb
```

### Чтение **до** репликации (мастер)
```bash
pgbench -T 60 -S -h localhost -p 5432 -U readonly appdb
```
Отметьте утилизацию CPU/IO мастера (`docker stats pg-primary`).

### Чтение **после** репликации (слейвы через Pgpool)
```bash
pgbench -T 60 -S -h localhost -p 9999 -U readonly appdb
```
Нагрузка должна сместиться на `pg-replica1`/`pg-replica2`, что видно по `docker stats` или `pg_stat_activity` на репликах.

### Запись под синхронной репликацией
```bash
pgbench -T 120 -N -h localhost -p 5432 -U app appdb
```
Параметр `synchronous_standby_names='FIRST 1 (...)'` гарантирует, что каждая транзакция подтверждается минимум одной репликой.

## Эксперимент с аварией мастера

1. Запустите длительную запись:
   ```bash
   pgbench -T 120 -N -h localhost -p 5432 -U app appdb
   ```
2. Остановите одну реплику (имитируем сбой):
   ```bash
   docker stop pg-replica1
   ```
3. Дождитесь завершения нагрузки и зафиксируйте количество строк:
   ```bash
   docker exec -it pg-primary psql -U app -d appdb -c "select count(*) from pgbench_accounts;"
   ```
4. Убейте мастер:
   ```bash
   docker stop pg-primary
   ```
5. Промоутите свежую реплику (в примере `pg-replica2`):
   ```bash
   ./replication/homework/tools/promote_replica.sh pg-replica2
   ```
6. Переключите вторую реплику на новый мастер (очистите её данные и запустите снова, чтобы она взяла бэкап уже с промоутнутого узла).
7. Проверьте количество строк на новом мастере и убедитесь, что потерь нет:
   ```bash
   docker exec -it pg-replica2 psql -U app -d appdb -c "select count(*) from pgbench_accounts;"
   ```

При включённой кворумной синхронной репликации транзакции не теряются: мастер ждёт подтверждения хотя бы одного standby. Для сравнения можно временно отключить синхронность (`synchronous_commit=local` и пустой `synchronous_standby_names`) и повторить эксперимент — тогда часть записей пропадёт после аварии мастера.

## Полезные команды

- Проверить, куда Pgpool отправляет запросы:
  ```bash
  docker exec -it pgpool sh -c "show pool_nodes;"
  ```
- Синхронность и задержки на мастере:
  ```bash
  docker exec -it pg-primary psql -U app -d appdb \
    -c "select application_name, state, sync_state, write_lag, flush_lag, replay_lag from pg_stat_replication;"
  ```
- Прямая проверка чтения с реплики:
  ```bash
  docker exec -it pg-replica1 psql -U readonly -d appdb -c "select count(*) from users;"
  ```

## Отчётность

- Код и конфигурация: каталог `replication/homework`.
- Запуск: `docker compose -f replication/homework/docker-compose.yml up -d`.
- Для сдачи ДЗ приложите логи нагрузочного теста и скриншоты/показания `docker stats`/`pg_stat_replication`, демонстрирующие смещение нагрузки на слейвы и отсутствие потерь транзакций при синхронной репликации.

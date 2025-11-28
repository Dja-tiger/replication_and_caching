#!/bin/bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${PURPLE}================================================${NC}"
    echo -e "${PURPLE}     🎬 ДЕМО КЭШИРОВАНИЯ E-COMMERCE     🎬${NC}"
    echo -e "${PURPLE}================================================${NC}"
}

print_section() {
    echo -e "\n${CYAN}$1${NC}"
    echo -e "${CYAN}$(printf '%.0s-' {1..50})${NC}"
}

print_demo_step() {
    echo -e "\n${YELLOW}📋 $1${NC}"
    echo -e "${BLUE}   $2${NC}"
}

wait_for_enter() {
    echo -e "\n${GREEN}Press Enter to continue...${NC}"
    read
}

# Демонстрация Cache-Aside паттерна
demo_cache_aside() {
    print_section "🏪 Cache-Aside Pattern - Рекомендации"

    print_demo_step "Шаг 1: Первый запрос (Cache Miss)" \
        "Данные загружаются из БД и сохраняются в кэш"

    echo "📡 Запрос рекомендаций для пользователя 1..."
    time curl -s "http://localhost/api/recommendations?user_id=1" | jq '.[0:2]' || curl -s "http://localhost/api/recommendations?user_id=1"

    wait_for_enter

    print_demo_step "Шаг 2: Второй запрос (Cache Hit)" \
        "Данные возвращаются из кэша (быстрее)"

    echo "📡 Повторный запрос рекомендаций..."
    time curl -s "http://localhost/api/recommendations?user_id=1" | jq '.[0:2]' || curl -s "http://localhost/api/recommendations?user_id=1"

    wait_for_enter

    print_demo_step "Шаг 3: Инвалидация кэша" \
        "Принудительная очистка кэша рекомендаций"

    echo "🗑️ Инвалидация кэша рекомендаций..."
    curl -s -X POST "http://localhost/api/cache/invalidate" \
        -H "Content-Type: application/json" \
        -d '{"cache_type": "recommendations"}' | jq . || echo "Cache invalidated"

    wait_for_enter
}

# Демонстрация Write-Through паттерна
demo_write_through() {
    print_section "🛒 Write-Through Pattern - Корзина"

    print_demo_step "Шаг 1: Просмотр текущей корзины" \
        "Загрузка данных корзины"

    echo "👀 Просмотр корзины..."
    curl -s "http://localhost/api/cart" | jq . || curl -s "http://localhost/api/cart"

    wait_for_enter

    print_demo_step "Шаг 2: Добавление товара (Write-Through)" \
        "Запись в БД и кэш одновременно"

    echo "➕ Добавление товара в корзину..."
    curl -s -X POST "http://localhost/api/cart/add" \
        -H "Content-Type: application/json" \
        -d '{"product_id": 1, "quantity": 2}' | jq . || echo "Product added"

    wait_for_enter

    print_demo_step "Шаг 3: Проверка обновленной корзины" \
        "Данные читаются из кэша"

    echo "🔍 Проверка корзины после добавления..."
    curl -s "http://localhost/api/cart" | jq . || curl -s "http://localhost/api/cart"

    wait_for_enter
}

# Демонстрация Refresh-Ahead паттерна
demo_refresh_ahead() {
    print_section "🏆 Refresh-Ahead Pattern - Бестселлеры"

    print_demo_step "Шаг 1: Запрос бестселлеров" \
        "Проактивное обновление кэша в фоне"

    echo "🏆 Запрос бестселлеров..."
    curl -s "http://localhost/api/bestsellers" | jq '.[0:3]' || curl -s "http://localhost/api/bestsellers"

    wait_for_enter

    print_demo_step "Информация о Refresh-Ahead" \
        "Кэш автоматически обновляется за 10 минут до истечения TTL"

    echo -e "${YELLOW}💡 Особенности Refresh-Ahead:${NC}"
    echo -e "${GREEN}  ✓ TTL: 1 час для бестселлеров${NC}"
    echo -e "${GREEN}  ✓ Обновление: за 10 минут до истечения${NC}"
    echo -e "${GREEN}  ✓ Пользователь всегда получает быстрый ответ${NC}"
    echo -e "${GREEN}  ✓ БД загружается равномерно${NC}"

    wait_for_enter
}

# Демонстрация Event-based инвалидации
demo_event_based() {
    print_section "⚡ Event-Based Pattern - Flash Sales"

    print_demo_step "Шаг 1: Загрузка Flash Sales" \
        "Кэш с коротким TTL (5 минут)"

    echo "⚡ Запрос flash sales..."
    curl -s "http://localhost/api/flash-sales" | jq . || curl -s "http://localhost/api/flash-sales"

    wait_for_enter

    print_demo_step "Шаг 2: Event-based инвалидация" \
        "Мгновенная инвалидация при изменении"

    echo "🔥 Инвалидация flash sales..."
    curl -s -X POST "http://localhost/api/cache/invalidate" \
        -H "Content-Type: application/json" \
        -d '{"cache_type": "flash-sales"}' | jq . || echo "Flash sales cache invalidated"

    echo -e "\n${YELLOW}💡 Event-based особенности:${NC}"
    echo -e "${GREEN}  ✓ Мгновенная инвалидация${NC}"
    echo -e "${GREEN}  ✓ WebSocket уведомления${NC}"
    echo -e "${GREEN}  ✓ Короткий TTL для динамических данных${NC}"

    wait_for_enter
}

# Мониторинг кэша в реальном времени
demo_cache_monitoring() {
    print_section "📊 Мониторинг кэша"

    print_demo_step "Статус всех кэшей" \
        "Просмотр TTL и состояния кэшированных данных"

    echo "📈 Статус кэшей..."
    curl -s "http://localhost/api/cache/status" | jq . || curl -s "http://localhost/api/cache/status"

    wait_for_enter

    print_demo_step "Доступные инструменты мониторинга" \
        "Grafana, Prometheus, Redis Commander"

    echo -e "${PURPLE}🔗 Полезные ссылки для мониторинга:${NC}"
    echo -e "${CYAN}  📊 Grafana Dashboard: http://localhost:3000${NC}"
    echo -e "${CYAN}  📈 Prometheus: http://localhost:9090${NC}"
    echo -e "${CYAN}  🔴 Redis Commander: http://localhost:8003${NC}"
    echo -e "${CYAN}  📋 Метрики приложения: http://localhost:8080/metrics${NC}"

    wait_for_enter
}

# Демонстрация WebSocket уведомлений
demo_websocket() {
    print_section "🔌 WebSocket Real-time Updates"

    print_demo_step "WebSocket подключение" \
        "Откройте браузер на http://localhost для демонстрации"

    echo -e "${YELLOW}💡 Что демонстрируется:${NC}"
    echo -e "${GREEN}  ✓ Real-time уведомления об изменениях${NC}"
    echo -e "${GREEN}  ✓ Обновление UI при инвалидации кэша${NC}"
    echo -e "${GREEN}  ✓ Статус соединения в реальном времени${NC}"

    echo -e "\n${CYAN}🌐 Откройте http://localhost в браузере${NC}"
    echo -e "${CYAN}🔌 WebSocket автоматически подключится${NC}"

    wait_for_enter
}

# Полное демо с нагрузочным тестированием
demo_performance() {
    print_section "🚀 Нагрузочное тестирование кэша"

    print_demo_step "Подготовка к нагрузочному тесту" \
        "Сравнение производительности с кэшем и без"

    # Очищаем кэш
    curl -s -X POST "http://localhost/api/cache/invalidate" \
        -H "Content-Type: application/json" \
        -d '{"cache_type": "all"}' > /dev/null

    echo "🧹 Кэш очищен"

    print_demo_step "Тест 1: Холодный кэш (10 запросов)" \
        "Первые запросы будут медленными"

    echo "❄️ Холодный кэш..."
    for i in {1..10}; do
        time_result=$(time (curl -s "http://localhost/api/bestsellers" > /dev/null) 2>&1 | grep real)
        echo "  Запрос $i: $time_result"
    done

    wait_for_enter

    print_demo_step "Тест 2: Горячий кэш (10 запросов)" \
        "Запросы будут быстрыми благодаря кэшу"

    echo "🔥 Горячий кэш..."
    for i in {1..10}; do
        time_result=$(time (curl -s "http://localhost/api/bestsellers" > /dev/null) 2>&1 | grep real)
        echo "  Запрос $i: $time_result"
    done

    wait_for_enter
}

# Главное меню
show_menu() {
    print_header

    echo -e "${YELLOW}Выберите демонстрацию:${NC}"
    echo "1) 🏪 Cache-Aside Pattern (Рекомендации)"
    echo "2) 🛒 Write-Through Pattern (Корзина)"
    echo "3) 🏆 Refresh-Ahead Pattern (Бестселлеры)"
    echo "4) ⚡ Event-Based Pattern (Flash Sales)"
    echo "5) 📊 Мониторинг кэша"
    echo "6) 🔌 WebSocket демо"
    echo "7) 🚀 Нагрузочное тестирование"
    echo "8) 🎬 Полное демо (все паттерны)"
    echo "0) 🚪 Выход"

    echo -e "\n${GREEN}Выберите номер [0-8]:${NC}"
    read choice

    case $choice in
        1) demo_cache_aside ;;
        2) demo_write_through ;;
        3) demo_refresh_ahead ;;
        4) demo_event_based ;;
        5) demo_cache_monitoring ;;
        6) demo_websocket ;;
        7) demo_performance ;;
        8)
            demo_cache_aside
            demo_write_through
            demo_refresh_ahead
            demo_event_based
            demo_cache_monitoring
            demo_websocket
            ;;
        0)
            echo -e "${GREEN}👋 До свидания!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Неверный выбор${NC}"
            wait_for_enter
            ;;
    esac
}

# Проверка готовности системы
check_system() {
    if ! curl -s "http://localhost/api/bestsellers" > /dev/null; then
        echo -e "${RED}❌ Система не готова. Запустите сначала:${NC}"
        echo -e "${CYAN}   ./scripts/start.sh${NC}"
        exit 1
    fi
}

# Главная функция
main() {
    check_system

    while true; do
        clear
        show_menu
        wait_for_enter
    done
}

# Запуск
main "$@"
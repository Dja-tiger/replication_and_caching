#!/bin/bash

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Функция для красивого вывода
print_header() {
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}  🛒 E-COMMERCE DEMO WITH ADVANCED CACHING  🛒${NC}"
    echo -e "${BLUE}================================================${NC}"
}

print_section() {
    echo -e "\n${CYAN}$1${NC}"
    echo -e "${CYAN}$(printf '%.0s-' {1..50})${NC}"
}

print_url() {
    echo -e "${GREEN}  ✓ $1:${NC} $2"
}

print_warning() {
    echo -e "${YELLOW}  ⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}  ✗ $1${NC}"
}

# Проверка зависимостей
check_dependencies() {
    print_section "Проверка зависимостей"

    if ! command -v docker &> /dev/null; then
        print_error "Docker не установлен"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose не установлен"
        exit 1
    fi

    print_url "Docker" "$(docker --version)"
    print_url "Docker Compose" "$(docker-compose --version)"
}

# Остановка существующих контейнеров
stop_existing() {
    print_section "Остановка существующих контейнеров"
    docker-compose down --remove-orphans 2>/dev/null || true
    echo -e "${GREEN}  ✓ Существующие контейнеры остановлены${NC}"
}

# Сборка и запуск
build_and_start() {
    print_section "Сборка и запуск сервисов"

    echo "🔨 Сборка образов..."
    docker-compose build --no-cache

    echo "🚀 Запуск сервисов..."
    docker-compose up -d

    # Ожидание готовности сервисов
    echo "⏳ Ожидание готовности сервисов..."
    sleep 10

    # Проверка состояния контейнеров
    echo "📊 Проверка состояния контейнеров:"
    docker-compose ps
}

# Отображение URLs
show_urls() {
    print_section "🌐 Доступные сервисы"

    echo -e "${PURPLE}ОСНОВНЫЕ СЕРВИСЫ:${NC}"
    print_url "🛒 Интернет-магазин" "http://localhost"
    print_url "🔌 WebSocket подключение" "ws://localhost/ws"
    print_url "🔥 Прямое API подключение" "http://localhost:8080"

    echo -e "\n${PURPLE}МОНИТОРИНГ И МЕТРИКИ:${NC}"
    print_url "📊 Grafana Dashboard" "http://localhost:3001/d/2b9e55e0-f1d5-4694-84de-7096d123e108/e-commerce-metrics (admin/admin)"
    print_url "📈 Prometheus" "http://localhost:9090"
    print_url "📋 Метрики приложения" "http://localhost:8080/metrics"

    echo -e "\n${PURPLE}УПРАВЛЕНИЕ БАЗАМИ ДАННЫХ:${NC}"
    print_url "🐘 pgAdmin (PostgreSQL)" "http://localhost:8002 (admin@demo.com/admin)"
    print_url "🔴 Redis Commander" "http://localhost:8003"
    print_url "🔍 Redis Insight" "http://localhost:8001"

    echo -e "\n${PURPLE}ПРЯМЫЕ ПОДКЛЮЧЕНИЯ:${NC}"
    print_url "🐘 PostgreSQL" "localhost:5432 (demo_user/demo_pass/ecommerce_db)"
    print_url "🔴 Redis" "localhost:6379"

    echo -e "\n${PURPLE}API ENDPOINTS (примеры):${NC}"
    print_url "🏆 Бестселлеры (Refresh-Ahead)" "http://localhost/api/bestsellers"
    print_url "💡 Рекомендации (Cache-Aside)" "http://localhost/api/recommendations"
    print_url "⚡ Flash Sales (Event-based)" "http://localhost/api/flash-sales"
    print_url "💬 Топ комментарии" "http://localhost/api/comments/top"
    print_url "🛒 Корзина (Write-Through)" "http://localhost/api/cart"
    print_url "📊 Статус кэшей" "http://localhost/api/cache/status"
}

# Демонстрация возможностей кэширования
show_caching_demo() {
    print_section "🧪 Демонстрация паттернов кэширования"

    echo -e "${PURPLE}РЕАЛИЗОВАННЫЕ ПАТТЕРНЫ:${NC}"
    echo -e "${GREEN}  ✓ Cache-Aside${NC} - Рекомендации (персонализированные)"
    echo -e "${GREEN}  ✓ Write-Through${NC} - Корзина и профиль пользователя"
    echo -e "${GREEN}  ✓ Refresh-Ahead${NC} - Бестселлеры (проактивное обновление)"
    echo -e "${GREEN}  ✓ Event-based${NC} - Flash sales (мгновенная инвалидация)"

    echo -e "\n${PURPLE}СТРАТЕГИИ ИНВАЛИДАЦИИ:${NC}"
    echo -e "${GREEN}  ✓ TTL${NC} - Автоматическое истечение (1 час для бестселлеров)"
    echo -e "${GREEN}  ✓ Tag-based${NC} - Групповая инвалидация рекомендаций"
    echo -e "${GREEN}  ✓ Event-driven${NC} - WebSocket уведомления при изменениях"

    echo -e "\n${PURPLE}ТЕСТИРОВАНИЕ:${NC}"
    echo -e "${CYAN}  Откройте Grafana Dashboard для мониторинга метрик кэширования${NC}"
    echo -e "${CYAN}  Используйте Redis Commander для просмотра кэшированных данных${NC}"
    echo -e "${CYAN}  Тестируйте инвалидацию через кнопки управления на главной странице${NC}"
}

# Полезные команды
show_useful_commands() {
    print_section "💡 Полезные команды"

    echo -e "${PURPLE}ОСТАНОВКА И ОЧИСТКА:${NC}"
    echo -e "${CYAN}  ./scripts/stop.sh${NC} - Остановить все сервисы"
    echo -e "${CYAN}  docker-compose down -v${NC} - Остановить + удалить volumes"
    echo -e "${CYAN}  docker system prune -a${NC} - Очистить все неиспользуемые образы"

    echo -e "\n${PURPLE}ЛОГИ И МОНИТОРИНГ:${NC}"
    echo -e "${CYAN}  docker-compose logs -f app${NC} - Логи приложения"
    echo -e "${CYAN}  docker-compose logs -f redis${NC} - Логи Redis"
    echo -e "${CYAN}  docker stats${NC} - Использование ресурсов"

    echo -e "\n${PURPLE}ОТЛАДКА:${NC}"
    echo -e "${CYAN}  docker-compose exec app sh${NC} - Войти в контейнер приложения"
    echo -e "${CYAN}  docker-compose exec redis redis-cli${NC} - Redis CLI"
    echo -e "${CYAN}  docker-compose exec postgres psql -U demo_user -d ecommerce_db${NC} - PostgreSQL CLI"
}

# Главная функция
main() {
    clear
    print_header

    check_dependencies
    stop_existing
    build_and_start

    # Дополнительная проверка готовности
    echo "🔍 Проверка готовности сервисов..."
    sleep 5

    # Проверяем доступность основных сервисов
    if curl -s http://localhost:8080/api/bestsellers > /dev/null; then
        echo -e "${GREEN}✓ Backend API готов${NC}"
    else
        print_warning "Backend API может быть еще не готов, подождите немного"
    fi

    if curl -s http://localhost > /dev/null; then
        echo -e "${GREEN}✓ Nginx готов${NC}"
    else
        print_warning "Nginx может быть еще не готов"
    fi

    show_urls
    show_caching_demo
    show_useful_commands

    echo -e "\n${GREEN}🎉 Система успешно запущена!${NC}"
    echo -e "${YELLOW}💡 Для остановки используйте: ./scripts/stop.sh${NC}\n"
}

# Запуск
main "$@"
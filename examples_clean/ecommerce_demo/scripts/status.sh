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
    echo -e "${BLUE}================================================${NC}"
    echo -e "${BLUE}      📊 СТАТУС E-COMMERCE DEMO СТЕКА      📊${NC}"
    echo -e "${BLUE}================================================${NC}"
}

print_section() {
    echo -e "\n${CYAN}$1${NC}"
    echo -e "${CYAN}$(printf '%.0s-' {1..50})${NC}"
}

print_service_status() {
    local service=$1
    local url=$2
    local expected_code=${3:-200}

    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "$expected_code"; then
        echo -e "${GREEN}  ✓ $service${NC} - Работает"
    else
        echo -e "${RED}  ✗ $service${NC} - Недоступен"
    fi
}

# Проверка состояния контейнеров
check_containers() {
    print_section "🐳 Состояние контейнеров"

    # Получаем информацию о контейнерах проекта
    containers=$(docker-compose ps --format "table {{.Name}}\t{{.State}}\t{{.Ports}}" 2>/dev/null)

    if [ $? -eq 0 ] && [ -n "$containers" ]; then
        echo "$containers"
    else
        echo -e "${RED}  ✗ Контейнеры не запущены или docker-compose.yml не найден${NC}"
        return 1
    fi
}

# Проверка доступности сервисов
check_services() {
    print_section "🌐 Доступность сервисов"

    echo -e "${PURPLE}Основные сервисы:${NC}"
    print_service_status "Nginx (Frontend)" "http://localhost"
    print_service_status "Go Backend API" "http://localhost:8080/api/bestsellers"
    print_service_status "WebSocket" "http://localhost/ws" 404  # WebSocket возвращает 404 на GET

    echo -e "\n${PURPLE}Мониторинг:${NC}"
    print_service_status "Prometheus" "http://localhost:9090"
    print_service_status "Grafana" "http://localhost:3001"
    echo -e "${CYAN}  📊 Dashboard: http://localhost:3001/d/2b9e55e0-f1d5-4694-84de-7096d123e108/e-commerce-metrics${NC}"

    echo -e "\n${PURPLE}Управление БД:${NC}"
    print_service_status "pgAdmin" "http://localhost:8002"
    print_service_status "Redis Commander" "http://localhost:8003"
    print_service_status "Redis Insight" "http://localhost:8001"
}

# Проверка API endpoints
check_api_endpoints() {
    print_section "🔌 API Endpoints"

    echo -e "${PURPLE}Кэширование паттерны:${NC}"

    # Бестселлеры (Refresh-Ahead)
    if response=$(curl -s -w "HTTPSTATUS:%{http_code}" "http://localhost/api/bestsellers"); then
        http_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
        if [ "$http_code" = "200" ]; then
            strategy=$(echo "$response" | grep -o '"X-Cache-Strategy":"[^"]*"' | cut -d'"' -f4)
            echo -e "${GREEN}  ✓ Бестселлеры${NC} (Refresh-Ahead) - $strategy"
        else
            echo -e "${RED}  ✗ Бестселлеры${NC} - HTTP $http_code"
        fi
    else
        echo -e "${RED}  ✗ Бестселлеры${NC} - Недоступен"
    fi

    # Рекомендации (Cache-Aside)
    if response=$(curl -s -w "HTTPSTATUS:%{http_code}" "http://localhost/api/recommendations"); then
        http_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
        if [ "$http_code" = "200" ]; then
            echo -e "${GREEN}  ✓ Рекомендации${NC} (Cache-Aside)"
        else
            echo -e "${RED}  ✗ Рекомендации${NC} - HTTP $http_code"
        fi
    else
        echo -e "${RED}  ✗ Рекомендации${NC} - Недоступен"
    fi

    # Flash Sales (Event-based)
    if response=$(curl -s -w "HTTPSTATUS:%{http_code}" "http://localhost/api/flash-sales"); then
        http_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
        if [ "$http_code" = "200" ]; then
            echo -e "${GREEN}  ✓ Flash Sales${NC} (Event-based)"
        else
            echo -e "${RED}  ✗ Flash Sales${NC} - HTTP $http_code"
        fi
    else
        echo -e "${RED}  ✗ Flash Sales${NC} - Недоступен"
    fi

    # Корзина (Write-Through)
    if response=$(curl -s -w "HTTPSTATUS:%{http_code}" "http://localhost/api/cart"); then
        http_code=$(echo $response | tr -d '\n' | sed -e 's/.*HTTPSTATUS://')
        if [ "$http_code" = "200" ]; then
            echo -e "${GREEN}  ✓ Корзина${NC} (Write-Through)"
        else
            echo -e "${RED}  ✗ Корзина${NC} - HTTP $http_code"
        fi
    else
        echo -e "${RED}  ✗ Корзина${NC} - Недоступен"
    fi
}

# Проверка состояния кэша
check_cache_status() {
    print_section "🗄️ Состояние кэша"

    if cache_response=$(curl -s "http://localhost/api/cache/status" 2>/dev/null); then
        echo -e "${GREEN}Статус кэшей получен:${NC}"
        echo "$cache_response" | python3 -m json.tool 2>/dev/null || echo "$cache_response"
    else
        echo -e "${RED}  ✗ Не удалось получить статус кэша${NC}"
    fi
}

# Использование ресурсов
check_resource_usage() {
    print_section "💾 Использование ресурсов"

    if command -v docker &> /dev/null; then
        echo -e "${PURPLE}Топ контейнеров по использованию ресурсов:${NC}"
        docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" | head -10
    else
        echo -e "${RED}  ✗ Docker не доступен${NC}"
    fi
}

# Проверка логов
check_recent_logs() {
    print_section "📝 Последние логи"

    echo -e "${PURPLE}Последние 5 строк логов приложения:${NC}"
    docker-compose logs --tail=5 app 2>/dev/null || echo -e "${RED}  ✗ Логи недоступны${NC}"

    echo -e "\n${PURPLE}Последние 3 строки логов Redis:${NC}"
    docker-compose logs --tail=3 redis 2>/dev/null || echo -e "${RED}  ✗ Логи Redis недоступны${NC}"
}

# Полезные команды для диагностики
show_diagnostic_commands() {
    print_section "🔧 Команды для диагностики"

    echo -e "${PURPLE}Просмотр логов:${NC}"
    echo -e "${CYAN}  docker-compose logs -f app${NC}       - Логи приложения"
    echo -e "${CYAN}  docker-compose logs -f redis${NC}     - Логи Redis"
    echo -e "${CYAN}  docker-compose logs -f prometheus${NC} - Логи Prometheus"

    echo -e "\n${PURPLE}Отладка контейнеров:${NC}"
    echo -e "${CYAN}  docker-compose exec app sh${NC}       - Вход в контейнер приложения"
    echo -e "${CYAN}  docker-compose exec redis redis-cli${NC} - Redis CLI"
    echo -e "${CYAN}  docker-compose exec postgres psql -U demo_user -d ecommerce_db${NC} - PostgreSQL CLI"

    echo -e "\n${PURPLE}Перезапуск сервисов:${NC}"
    echo -e "${CYAN}  docker-compose restart app${NC}       - Перезапуск приложения"
    echo -e "${CYAN}  docker-compose restart nginx${NC}     - Перезапуск Nginx"
}

# Главная функция
main() {
    clear
    print_header

    # Проверяем базовую доступность Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}✗ Docker не установлен${NC}"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}✗ Docker Compose не установлен${NC}"
        exit 1
    fi

    check_containers

    # Если контейнеры запущены, проверяем сервисы
    if [ $? -eq 0 ]; then
        check_services
        check_api_endpoints
        check_cache_status
        check_resource_usage
        check_recent_logs
    fi

    show_diagnostic_commands

    echo -e "\n${GREEN}📊 Проверка статуса завершена!${NC}\n"
}

# Запуск
main "$@"
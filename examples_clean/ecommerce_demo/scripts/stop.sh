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
    echo -e "${RED}================================================${NC}"
    echo -e "${RED}     🛑 ОСТАНОВКА E-COMMERCE DEMO СТЕКА     🛑${NC}"
    echo -e "${RED}================================================${NC}"
}

print_section() {
    echo -e "\n${CYAN}$1${NC}"
    echo -e "${CYAN}$(printf '%.0s-' {1..50})${NC}"
}

print_status() {
    echo -e "${GREEN}  ✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}  ⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}  ℹ $1${NC}"
}

# Остановка сервисов
stop_services() {
    print_section "Остановка сервисов"

    echo "🛑 Остановка контейнеров..."
    docker-compose down

    print_status "Все контейнеры остановлены"
}

# Опциональная очистка
cleanup_option() {
    print_section "Опции очистки"

    echo -e "${YELLOW}Выберите уровень очистки:${NC}"
    echo "1) Только остановка (сохранить данные)"
    echo "2) Остановка + удаление volumes (удалить все данные)"
    echo "3) Полная очистка (удалить образы и volumes)"
    echo "q) Пропустить очистку"

    read -p "Ваш выбор [1-3, q]: " choice

    case $choice in
        1)
            print_info "Данные сохранены в volumes"
            ;;
        2)
            echo "🗑️ Удаление volumes..."
            docker-compose down -v
            print_status "Volumes удалены"
            print_warning "Все данные БД и кэша удалены"
            ;;
        3)
            echo "🗑️ Полная очистка..."
            docker-compose down -v --rmi all
            print_status "Образы и volumes удалены"
            print_warning "Потребуется пересборка при следующем запуске"
            ;;
        q|Q)
            print_info "Очистка пропущена"
            ;;
        *)
            print_warning "Неверный выбор, очистка пропущена"
            ;;
    esac
}

# Информация о состоянии
show_status() {
    print_section "Состояние системы"

    # Проверяем запущенные контейнеры проекта
    running_containers=$(docker ps --filter "name=ecommerce_" --format "table {{.Names}}\t{{.Status}}" | tail -n +2)

    if [ -z "$running_containers" ]; then
        print_status "Все контейнеры E-commerce Demo остановлены"
    else
        print_warning "Некоторые контейнеры все еще запущены:"
        echo "$running_containers"
    fi

    # Проверяем volumes
    volumes=$(docker volume ls --filter "name=ecommerce_demo" --format "table {{.Name}}" | tail -n +2)
    if [ -n "$volumes" ]; then
        print_info "Сохраненные volumes:"
        echo "$volumes"
    fi
}

# Полезная информация
show_restart_info() {
    print_section "💡 Для повторного запуска"

    echo -e "${CYAN}Быстрый запуск:${NC}"
    echo -e "${GREEN}  ./scripts/start.sh${NC}"

    echo -e "\n${CYAN}Сборка с нуля:${NC}"
    echo -e "${GREEN}  docker-compose build --no-cache${NC}"
    echo -e "${GREEN}  docker-compose up -d${NC}"

    echo -e "\n${CYAN}Просмотр логов последнего запуска:${NC}"
    echo -e "${GREEN}  docker-compose logs${NC}"
}

# Очистка системы Docker (опционально)
system_cleanup_option() {
    print_section "🧹 Системная очистка Docker"

    echo -e "${YELLOW}Хотите выполнить общую очистку Docker? [y/N]:${NC}"
    read -p "" cleanup_choice

    case $cleanup_choice in
        y|Y|yes|YES)
            echo "🧹 Выполнение системной очистки Docker..."
            docker system prune -f
            print_status "Неиспользуемые образы, контейнеры и сети удалены"
            ;;
        *)
            print_info "Системная очистка пропущена"
            ;;
    esac
}

# Главная функция
main() {
    clear
    print_header

    stop_services
    show_status
    cleanup_option
    system_cleanup_option
    show_restart_info

    echo -e "\n${GREEN}✅ Остановка завершена!${NC}"
    echo -e "${BLUE}📝 Все логи сохранены в Docker${NC}\n"
}

# Запуск
main "$@"
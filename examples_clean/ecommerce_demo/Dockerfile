# Multi-stage build для оптимизации размера образа
FROM golang:1.21-alpine AS builder

# Устанавливаем необходимые пакеты
RUN apk add --no-cache git wget

# Создаем рабочую директорию
WORKDIR /app

# Копируем go mod файлы
COPY backend/go.mod backend/go.sum ./

# Загружаем зависимости
RUN go mod download

# Копируем исходный код
COPY backend/ ./

# Собираем приложение
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main .

# Второй этап - создание минимального образа
FROM alpine:latest

# Устанавливаем ca-certificates для HTTPS запросов и wget для healthcheck
RUN apk --no-cache add ca-certificates wget

WORKDIR /app

# Копируем скомпилированное приложение
COPY --from=builder /app/main .

# Копируем статические файлы
COPY static/ ./static/

# Создаем пользователя для безопасности
RUN adduser -D -s /bin/sh appuser
USER appuser

# Открываем порт
EXPOSE 8080

# Запускаем приложение
CMD ["./main"]
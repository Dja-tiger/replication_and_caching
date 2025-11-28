package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"github.com/gorilla/mux"
	"github.com/gorilla/websocket"
	"github.com/prometheus/client_golang/prometheus/promhttp"

	"ecommerce-backend/cache"
	"ecommerce-backend/handlers"
	"ecommerce-backend/middleware"
	"ecommerce-backend/metrics"
	"ecommerce-backend/models"
	"ecommerce-backend/services"
)

type Server struct {
	router    *mux.Router
	db        *services.DatabaseService
	cache     *cache.CacheService
	handlers  *handlers.Handlers
	wsClients map[*websocket.Conn]bool
	wsMutex   sync.RWMutex
	upgrader  websocket.Upgrader
}

func main() {
	log.Println("Starting E-commerce Demo Server with advanced caching patterns...")

	// Инициализация сервисов
	server, err := initializeServer()
	if err != nil {
		log.Fatal("Failed to initialize server:", err)
	}
	defer server.cleanup()

	// Настройка маршрутов
	server.setupRoutes()

	// Создаем главный мультиплексор
	mainMux := http.NewServeMux()
	mainMux.HandleFunc("/ws", server.websocketHandler) // WebSocket без middleware
	mainMux.Handle("/", server.router) // Все остальное через router с middleware

	// Запуск HTTP сервера
	httpServer := &http.Server{
		Addr:         ":8080",
		Handler:      mainMux,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Graceful shutdown
	go func() {
		sigChan := make(chan os.Signal, 1)
		signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)
		<-sigChan

		log.Println("Shutting down server...")

		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()

		httpServer.Shutdown(ctx)
	}()

	log.Println("Server starting on http://localhost:8080")
	log.Println("Metrics available on http://localhost:8080/metrics")
	log.Println("WebSocket endpoint: ws://localhost:8080/ws")

	if err := httpServer.ListenAndServe(); err != http.ErrServerClosed {
		log.Fatal("Server failed:", err)
	}

	log.Println("Server stopped")
}

func initializeServer() (*Server, error) {
	// Инициализация базы данных
	dbService, err := services.NewDatabaseService(
		getEnv("DB_HOST", "localhost"),
		getEnv("DB_USER", "ecommerce_user"),
		getEnv("DB_PASSWORD", "ecommerce_password"),
		getEnv("DB_NAME", "ecommerce_db"),
		5432,
	)
	if err != nil {
		return nil, fmt.Errorf("failed to initialize database: %v", err)
	}

	// Миграция и заполнение данными
	if err := dbService.AutoMigrate(); err != nil {
		return nil, fmt.Errorf("failed to migrate database: %v", err)
	}

	if err := dbService.SeedData(); err != nil {
		return nil, fmt.Errorf("failed to seed database: %v", err)
	}

	// Инициализация кэша
	cacheService := cache.NewCacheService(
		getEnv("REDIS_HOST", "localhost")+":6379",
		getEnv("REDIS_PASSWORD", ""),
		0,
	)

	// Инициализация handlers
	handlersService := handlers.NewHandlers(dbService, cacheService)

	// WebSocket upgrader
	upgrader := websocket.Upgrader{
		CheckOrigin: func(r *http.Request) bool {
			return true // Разрешаем подключения с любых доменов для демо
		},
		ReadBufferSize:  1024,
		WriteBufferSize: 1024,
	}

	server := &Server{
		router:    mux.NewRouter(),
		db:        dbService,
		cache:     cacheService,
		handlers:  handlersService,
		wsClients: make(map[*websocket.Conn]bool),
		upgrader:  upgrader,
	}

	log.Println("Server initialized successfully")
	return server, nil
}

func (s *Server) setupRoutes() {
	// Применяем middleware для маршрутов
	s.router.Use(middleware.LoggingMiddleware)
	s.router.Use(middleware.CORSMiddleware)
	s.router.Use(middleware.PrometheusMiddleware)

	// API маршруты с различными паттернами кэширования
	api := s.router.PathPrefix("/api").Subrouter()

	// Бестселлеры - Refresh-Ahead pattern (проактивное обновление)
	api.HandleFunc("/bestsellers", s.getBestsellersHandler).Methods("GET")

	// Рекомендации - Cache-Aside pattern с персонализацией
	api.HandleFunc("/recommendations", s.getRecommendationsHandler).Methods("GET")

	// Flash sales - Event-based invalidation
	api.HandleFunc("/flash-sales", s.getFlashSalesHandler).Methods("GET")

	// Комментарии - Cache-Aside для редко изменяемых данных
	api.HandleFunc("/comments/top", s.getTopCommentsHandler).Methods("GET")

	// Продукты и пользователи
	api.HandleFunc("/product/{id}", s.getProductHandler).Methods("GET")
	// ВАЖНО: более специфичные маршруты должны идти ПЕРЕД общими
	api.HandleFunc("/user/profile", s.getProfileHandler).Methods("GET")
	api.HandleFunc("/user/profile", s.updateCurrentProfileHandler).Methods("PUT")
	api.HandleFunc("/user/{id}", s.getUserHandler).Methods("GET")
	api.HandleFunc("/user/{id}/profile", s.updateProfileHandler).Methods("PUT")

	// Корзина - Write-Through pattern
	api.HandleFunc("/cart", s.getCartHandler).Methods("GET")
	api.HandleFunc("/cart/add/{productId}", s.addToCartHandler).Methods("POST")
	api.HandleFunc("/cart/update", s.updateCartHandler).Methods("PUT")
	api.HandleFunc("/cart/remove/{productId}", s.removeFromCartHandler).Methods("DELETE")

	// Управление кэшем
	api.HandleFunc("/cache/invalidate/{cacheType}", s.invalidateCacheHandler).Methods("POST")
	api.HandleFunc("/cache/status", s.getCacheStatusHandler).Methods("GET")

	// Prometheus метрики
	s.router.Handle("/metrics", promhttp.Handler())

	// Статические файлы (будут обслуживаться nginx в production)
	s.router.PathPrefix("/static/").Handler(http.StripPrefix("/static/", http.FileServer(http.Dir("./static/"))))

	log.Println("Routes configured")
}

// WebSocket handler для real-time обновлений
func (s *Server) websocketHandler(w http.ResponseWriter, r *http.Request) {
	conn, err := s.upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("WebSocket upgrade failed: %v", err)
		return
	}
	defer conn.Close()

	// Добавляем клиента
	s.wsMutex.Lock()
	s.wsClients[conn] = true
	clientCount := len(s.wsClients)
	s.wsMutex.Unlock()

	metrics.SetActiveWebSocketConnections(clientCount)
	log.Printf("WebSocket client connected. Total clients: %d", clientCount)

	// Отправляем приветственное сообщение
	welcomeMsg := models.WSMessage{
		Type: "connection",
		Data: map[string]interface{}{
			"status":  "connected",
			"message": "Successfully connected to E-commerce WebSocket",
		},
	}
	conn.WriteJSON(welcomeMsg)

	// Читаем сообщения от клиента
	for {
		var msg models.WSMessage
		err := conn.ReadJSON(&msg)
		if err != nil {
			log.Printf("WebSocket read error: %v", err)
			break
		}

		metrics.RecordWebSocketMessage("inbound", msg.Type)

		// Обрабатываем сообщения от клиента
		switch msg.Type {
		case "ping":
			pongMsg := models.WSMessage{
				Type: "pong",
				Data: map[string]interface{}{"timestamp": time.Now()},
			}
			conn.WriteJSON(pongMsg)
			metrics.RecordWebSocketMessage("outbound", "pong")
		}
	}

	// Удаляем клиента при отключении
	s.wsMutex.Lock()
	delete(s.wsClients, conn)
	clientCount = len(s.wsClients)
	s.wsMutex.Unlock()

	metrics.SetActiveWebSocketConnections(clientCount)
	log.Printf("WebSocket client disconnected. Total clients: %d", clientCount)
}

// Рассылка сообщений всем подключенным WebSocket клиентам
func (s *Server) broadcastMessage(msgType string, data interface{}) {
	message := models.WSMessage{
		Type: msgType,
		Data: data,
	}

	s.wsMutex.RLock()
	defer s.wsMutex.RUnlock()

	for conn := range s.wsClients {
		err := conn.WriteJSON(message)
		if err != nil {
			log.Printf("WebSocket write error: %v", err)
			conn.Close()
			delete(s.wsClients, conn)
		} else {
			metrics.RecordWebSocketMessage("outbound", msgType)
		}
	}
}

// Делегируем handlers к соответствующему сервису
func (s *Server) getBestsellersHandler(w http.ResponseWriter, r *http.Request) {
	s.handlers.GetBestsellersHandler(w, r)
}

func (s *Server) getRecommendationsHandler(w http.ResponseWriter, r *http.Request) {
	s.handlers.GetRecommendationsHandler(w, r)
}

func (s *Server) getFlashSalesHandler(w http.ResponseWriter, r *http.Request) {
	s.handlers.GetFlashSalesHandler(w, r)
}

func (s *Server) getTopCommentsHandler(w http.ResponseWriter, r *http.Request) {
	s.handlers.GetTopCommentsHandler(w, r)
}

func (s *Server) getProductHandler(w http.ResponseWriter, r *http.Request) {
	s.handlers.GetProductHandler(w, r)
}

func (s *Server) getUserHandler(w http.ResponseWriter, r *http.Request) {
	s.handlers.GetUserHandler(w, r)
}

func (s *Server) getProfileHandler(w http.ResponseWriter, r *http.Request) {
	s.handlers.GetProfileHandler(w, r)
}

func (s *Server) updateProfileHandler(w http.ResponseWriter, r *http.Request) {
	s.handlers.UpdateProfileHandler(w, r)

	// Уведомляем WebSocket клиентов об обновлении профиля
	s.broadcastMessage("profile_updated", map[string]interface{}{
		"timestamp": time.Now(),
		"message":   "User profile updated",
	})
}

func (s *Server) updateCurrentProfileHandler(w http.ResponseWriter, r *http.Request) {
	s.handlers.UpdateCurrentProfileHandler(w, r)

	// Уведомляем WebSocket клиентов об обновлении профиля
	s.broadcastMessage("profile_updated", map[string]interface{}{
		"timestamp": time.Now(),
		"message":   "User profile updated",
	})
}

func (s *Server) getCartHandler(w http.ResponseWriter, r *http.Request) {
	s.handlers.GetCartHandler(w, r)
}

func (s *Server) addToCartHandler(w http.ResponseWriter, r *http.Request) {
	s.handlers.AddToCartHandler(w, r)

	// Уведомляем об изменении корзины
	s.broadcastMessage("cart_updated", map[string]interface{}{
		"action":    "add",
		"timestamp": time.Now(),
	})
}

func (s *Server) updateCartHandler(w http.ResponseWriter, r *http.Request) {
	s.handlers.UpdateCartHandler(w, r)

	s.broadcastMessage("cart_updated", map[string]interface{}{
		"action":    "update",
		"timestamp": time.Now(),
	})
}

func (s *Server) removeFromCartHandler(w http.ResponseWriter, r *http.Request) {
	s.handlers.RemoveFromCartHandler(w, r)

	s.broadcastMessage("cart_updated", map[string]interface{}{
		"action":    "remove",
		"timestamp": time.Now(),
	})
}

func (s *Server) invalidateCacheHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	cacheType := vars["cacheType"]

	s.handlers.InvalidateCacheHandler(w, r)

	// Уведомляем об инвалидации кэша
	s.broadcastMessage("cache_invalidated", map[string]interface{}{
		"cache":     cacheType,
		"timestamp": time.Now(),
		"message":   "Cache invalidated",
	})
}

func (s *Server) getCacheStatusHandler(w http.ResponseWriter, r *http.Request) {
	s.handlers.GetCacheStatusHandler(w, r)
}

func (s *Server) cleanup() {
	log.Println("Cleaning up resources...")

	// Закрываем все WebSocket соединения
	s.wsMutex.Lock()
	for conn := range s.wsClients {
		conn.Close()
	}
	s.wsClients = make(map[*websocket.Conn]bool)
	s.wsMutex.Unlock()

	// Закрываем кэш
	if s.cache != nil {
		s.cache.Close()
	}

	log.Println("Cleanup completed")
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}
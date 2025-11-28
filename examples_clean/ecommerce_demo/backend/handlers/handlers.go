package handlers

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strconv"
	"time"

	"github.com/gorilla/mux"
	"ecommerce-backend/cache"
	"ecommerce-backend/models"
	"ecommerce-backend/services"
	"ecommerce-backend/metrics"
)

type Handlers struct {
	db    *services.DatabaseService
	cache *cache.CacheService
}

func NewHandlers(db *services.DatabaseService, cache *cache.CacheService) *Handlers {
	return &Handlers{
		db:    db,
		cache: cache,
	}
}

// Публичные методы для вызова из main.go
func (h *Handlers) GetBestsellersHandler(w http.ResponseWriter, r *http.Request) {
	h.getBestsellersHandler(w, r)
}

func (h *Handlers) GetRecommendationsHandler(w http.ResponseWriter, r *http.Request) {
	h.getRecommendationsHandler(w, r)
}

func (h *Handlers) GetFlashSalesHandler(w http.ResponseWriter, r *http.Request) {
	h.getFlashSalesHandler(w, r)
}

func (h *Handlers) GetTopCommentsHandler(w http.ResponseWriter, r *http.Request) {
	h.getTopCommentsHandler(w, r)
}

func (h *Handlers) GetProductHandler(w http.ResponseWriter, r *http.Request) {
	h.getProductHandler(w, r)
}

func (h *Handlers) GetUserHandler(w http.ResponseWriter, r *http.Request) {
	h.getUserHandler(w, r)
}

func (h *Handlers) GetProfileHandler(w http.ResponseWriter, r *http.Request) {
	h.getProfileHandler(w, r)
}

func (h *Handlers) UpdateProfileHandler(w http.ResponseWriter, r *http.Request) {
	h.updateProfileHandler(w, r)
}

func (h *Handlers) UpdateCurrentProfileHandler(w http.ResponseWriter, r *http.Request) {
	h.updateCurrentProfileHandler(w, r)
}

func (h *Handlers) GetCartHandler(w http.ResponseWriter, r *http.Request) {
	h.getCartHandler(w, r)
}

func (h *Handlers) AddToCartHandler(w http.ResponseWriter, r *http.Request) {
	h.addToCartHandler(w, r)
}

func (h *Handlers) UpdateCartHandler(w http.ResponseWriter, r *http.Request) {
	h.updateCartHandler(w, r)
}

func (h *Handlers) RemoveFromCartHandler(w http.ResponseWriter, r *http.Request) {
	h.removeFromCartHandler(w, r)
}

func (h *Handlers) InvalidateCacheHandler(w http.ResponseWriter, r *http.Request) {
	h.invalidateCacheHandler(w, r)
}

func (h *Handlers) GetCacheStatusHandler(w http.ResponseWriter, r *http.Request) {
	h.getCacheStatusHandler(w, r)
}

func (h *Handlers) setupRoutes(r *mux.Router) {
	// API routes
	api := r.PathPrefix("/api").Subrouter()

	// Продукты с разными стратегиями кэширования
	api.HandleFunc("/bestsellers", h.getBestsellersHandler).Methods("GET")
	api.HandleFunc("/recommendations", h.getRecommendationsHandler).Methods("GET")
	api.HandleFunc("/flash-sales", h.getFlashSalesHandler).Methods("GET")
	api.HandleFunc("/comments/top", h.getTopCommentsHandler).Methods("GET")

	// Продукты и пользователи
	api.HandleFunc("/product/{id}", h.getProductHandler).Methods("GET")
	api.HandleFunc("/user/{id}", h.getUserHandler).Methods("GET")
	api.HandleFunc("/user/{id}/profile", h.updateProfileHandler).Methods("PUT")

	// Корзина (Write-Through pattern)
	api.HandleFunc("/cart", h.getCartHandler).Methods("GET")
	api.HandleFunc("/cart/add", h.addToCartHandler).Methods("POST")
	api.HandleFunc("/cart/update", h.updateCartHandler).Methods("PUT")
	api.HandleFunc("/cart/remove", h.removeFromCartHandler).Methods("DELETE")

	// Управление кэшем
	api.HandleFunc("/cache/invalidate", h.invalidateCacheHandler).Methods("POST")
	api.HandleFunc("/cache/status", h.getCacheStatusHandler).Methods("GET")

	// Метрики для Prometheus
	api.HandleFunc("/metrics", h.metricsHandler).Methods("GET")
}

// Cache-Aside + Refresh-Ahead для бестселлеров (стабильные данные)
func (h *Handlers) getBestsellersHandler(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		metrics.RecordHTTPRequest("GET", "/api/bestsellers", "200", time.Since(start).Seconds())
	}()

	// Используем Refresh-Ahead для проактивного обновления
	result, err := h.cache.GetBestsellersWithRefreshAhead(func() (interface{}, error) {
		log.Println("Fetching bestsellers from database (Refresh-Ahead)")
		products, err := h.db.GetBestsellers()
		if err != nil {
			return nil, err
		}
		metrics.RecordDatabaseQuery("SELECT", "products", time.Since(start).Seconds())
		return products, nil
	})

	if err != nil {
		// Если кэш не работает, идем напрямую в БД
		products, dbErr := h.db.GetBestsellers()
		if dbErr != nil {
			http.Error(w, dbErr.Error(), http.StatusInternalServerError)
			return
		}
		result = products
	}

	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-Cache-Strategy", "refresh-ahead")
	json.NewEncoder(w).Encode(result)
}

// Cache-Aside для персонализированных рекомендаций (Tag-based invalidation)
func (h *Handlers) getRecommendationsHandler(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		metrics.RecordHTTPRequest("GET", "/api/recommendations", "200", time.Since(start).Seconds())
	}()

	// Получаем userID из query параметров или используем дефолтный
	userIDStr := r.URL.Query().Get("user_id")
	userID := uint(1) // дефолтный пользователь
	if userIDStr != "" {
		if id, err := strconv.ParseUint(userIDStr, 10, 32); err == nil {
			userID = uint(id)
		}
	}

	// Cache-Aside паттерн для персонализированных данных
	result, err := h.cache.GetRecommendationsWithCacheAside(userID, func(uid uint) (interface{}, error) {
		log.Printf("Fetching recommendations from database for user %d (Cache-Aside)", uid)
		products, err := h.db.GetRecommendations(uid, 6)
		if err != nil {
			return nil, err
		}
		metrics.RecordDatabaseQuery("SELECT", "products", time.Since(start).Seconds())
		return products, nil
	})

	if err != nil {
		// Fallback к БД
		products, dbErr := h.db.GetRecommendations(userID, 6)
		if dbErr != nil {
			http.Error(w, dbErr.Error(), http.StatusInternalServerError)
			return
		}
		result = products
	}

	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-Cache-Strategy", "cache-aside-tags")
	w.Header().Set("X-User-ID", strconv.FormatUint(uint64(userID), 10))
	json.NewEncoder(w).Encode(result)
}

// Event-based invalidation для flash sales (динамические данные)
func (h *Handlers) getFlashSalesHandler(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		metrics.RecordHTTPRequest("GET", "/api/flash-sales", "200", time.Since(start).Seconds())
	}()

	var products []models.Product

	// Cache-Aside с коротким TTL для динамических данных
	err := h.cache.GetWithCacheAside("flash_sales", &products, func() (interface{}, error) {
		log.Println("Fetching flash sales from database (Cache-Aside)")
		result, err := h.db.GetFlashSales()
		if err != nil {
			return nil, err
		}
		metrics.RecordDatabaseQuery("SELECT", "products", time.Since(start).Seconds())
		return result, nil
	}, h.cache.GetTTLForDataType("flash_sales"))

	if err != nil {
		// Fallback к БД
		products, err = h.db.GetFlashSales()
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
	}

	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-Cache-Strategy", "event-based")
	json.NewEncoder(w).Encode(products)
}

// Cache-Aside для комментариев (редко изменяемые данные)
func (h *Handlers) getTopCommentsHandler(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		metrics.RecordHTTPRequest("GET", "/api/comments/top", "200", time.Since(start).Seconds())
	}()

	var comments []models.Comment

	err := h.cache.GetWithCacheAside("top_comments", &comments, func() (interface{}, error) {
		log.Println("Fetching top comments from database (Cache-Aside)")
		result, err := h.db.GetTopComments(5)
		if err != nil {
			return nil, err
		}
		metrics.RecordDatabaseQuery("SELECT", "comments", time.Since(start).Seconds())
		return result, nil
	}, h.cache.GetTTLForDataType("top_comments"))

	if err != nil {
		comments, err = h.db.GetTopComments(5)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
	}

	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-Cache-Strategy", "cache-aside")
	json.NewEncoder(w).Encode(comments)
}

// Write-Through паттерн для корзины (часто изменяемые данные)
func (h *Handlers) addToCartHandler(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		metrics.RecordHTTPRequest("POST", "/api/cart/add", "200", time.Since(start).Seconds())
		metrics.RecordCartOperation("add")
	}()

	// Получаем productId из URL
	vars := mux.Vars(r)
	productID, err := strconv.ParseUint(vars["productId"], 10, 32)
	if err != nil {
		http.Error(w, "Invalid product ID", http.StatusBadRequest)
		return
	}

	userID := uint(1) // Дефолтный пользователь
	quantity := 1     // По умолчанию добавляем 1 товар

	// Write-Through: записываем в БД и кэш одновременно
	cartKey := fmt.Sprintf("cart:%d", userID)

	err = h.cache.SetWithWriteThrough(cartKey, models.AddToCartRequest{ProductID: uint(productID), Quantity: quantity}, func(data interface{}) error {
		request := data.(models.AddToCartRequest)
		return h.db.AddToCart(userID, request.ProductID, request.Quantity)
	}, h.cache.GetTTLForDataType("cart"))

	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// Инвалидируем кэш корзины для обновления
	h.cache.Delete(fmt.Sprintf("cart_items:%d", userID))

	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-Cache-Strategy", "write-through")
	json.NewEncoder(w).Encode(map[string]string{"status": "success"})
}

func (h *Handlers) getCartHandler(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		metrics.RecordHTTPRequest("GET", "/api/cart", "200", time.Since(start).Seconds())
	}()

	userID := uint(1) // Дефолтный пользователь

	var cartResponse models.CartResponse

	// Cache-Aside для загрузки корзины
	cartKey := fmt.Sprintf("cart_items:%d", userID)
	err := h.cache.GetWithCacheAside(cartKey, &cartResponse, func() (interface{}, error) {
		log.Printf("Fetching cart from database for user %d (Cache-Aside)", userID)

		items, err := h.db.GetCartItems(userID)
		if err != nil {
			return models.CartResponse{}, err
		}

		total, count, err := h.db.GetCartTotal(userID)
		if err != nil {
			return models.CartResponse{}, err
		}

		metrics.RecordDatabaseQuery("SELECT", "cart", time.Since(start).Seconds())

		return models.CartResponse{
			Items: items,
			Total: total,
			Count: count,
		}, nil
	}, h.cache.GetTTLForDataType("cart"))

	if err != nil {
		// Fallback к БД
		items, dbErr := h.db.GetCartItems(userID)
		if dbErr != nil {
			http.Error(w, dbErr.Error(), http.StatusInternalServerError)
			return
		}

		total, count, _ := h.db.GetCartTotal(userID)
		cartResponse = models.CartResponse{
			Items: items,
			Total: total,
			Count: count,
		}
	}

	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("X-Cache-Strategy", "cache-aside")
	json.NewEncoder(w).Encode(cartResponse)
}

func (h *Handlers) invalidateCacheHandler(w http.ResponseWriter, r *http.Request) {
	start := time.Now()
	defer func() {
		metrics.RecordHTTPRequest("POST", "/api/cache/invalidate", "200", time.Since(start).Seconds())
	}()

	// Получаем cacheType из URL
	vars := mux.Vars(r)
	cacheType := vars["cacheType"]

	// Используем стратегию инвалидации
	err := h.cache.InvalidateWithStrategy(cacheType)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	log.Printf("Cache invalidated: %s", cacheType)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"status":     "success",
		"cache_type": cacheType,
		"timestamp":  time.Now(),
	})
}

func (h *Handlers) getCacheStatusHandler(w http.ResponseWriter, r *http.Request) {
	status := h.cache.GetCacheStatus()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(status)
}

// Другие handlers (упрощенные версии)
func (h *Handlers) getProductHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id, _ := strconv.ParseUint(vars["id"], 10, 32)

	product, err := h.db.GetProduct(uint(id))
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	metrics.RecordProductView(vars["id"])

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(product)
}

func (h *Handlers) getUserHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id, _ := strconv.ParseUint(vars["id"], 10, 32)

	user, err := h.db.GetUser(uint(id))
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(user)
}

// getProfileHandler возвращает профиль текущего пользователя (без ID)
func (h *Handlers) getProfileHandler(w http.ResponseWriter, r *http.Request) {
	// Используем дефолтного пользователя ID=1
	userID := uint(1)
	log.Printf("getProfileHandler called with userID: %d", userID)

	user, err := h.db.GetUser(userID)
	if err != nil {
		// Если пользователя нет, создаем дефолтного
		user = &models.User{
			ID:    userID,
			Name:  "User",
			Email: "user@example.com",
		}
	}

	response := map[string]interface{}{
		"user": user,
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(response)
}

func (h *Handlers) updateProfileHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	id, _ := strconv.ParseUint(vars["id"], 10, 32)

	var req models.UpdateProfileRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	// Write-Through для профиля пользователя
	err := h.cache.SetWithWriteThrough(fmt.Sprintf("profile:%d", id), req, func(data interface{}) error {
		request := data.(models.UpdateProfileRequest)
		return h.db.UpdateUser(uint(id), request.Name)
	}, h.cache.GetTTLForDataType("user_profile"))

	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "success"})
}

// updateCurrentProfileHandler обновляет профиль текущего пользователя (без ID)
func (h *Handlers) updateCurrentProfileHandler(w http.ResponseWriter, r *http.Request) {
	// Используем дефолтного пользователя ID=1
	userID := uint(1)

	var req models.UpdateProfileRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	// Write-Through для профиля пользователя
	err := h.cache.SetWithWriteThrough(fmt.Sprintf("profile:%d", userID), req, func(data interface{}) error {
		request := data.(models.UpdateProfileRequest)
		return h.db.UpdateUser(userID, request.Name)
	}, h.cache.GetTTLForDataType("user_profile"))

	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "success"})
}

func (h *Handlers) updateCartHandler(w http.ResponseWriter, r *http.Request) {
	var req models.UpdateCartRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

	userID := uint(1)

	// Write-Through для обновления корзины
	err := h.cache.SetWithWriteThrough(fmt.Sprintf("cart_update:%d:%d", userID, req.ProductID), req, func(data interface{}) error {
		request := data.(models.UpdateCartRequest)
		return h.db.UpdateCartItem(userID, request.ProductID, request.Quantity)
	}, h.cache.GetTTLForDataType("cart"))

	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// Инвалидируем кэш корзины
	h.cache.Delete(fmt.Sprintf("cart_items:%d", userID))

	metrics.RecordCartOperation("update")

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "success"})
}

func (h *Handlers) removeFromCartHandler(w http.ResponseWriter, r *http.Request) {
	// Получаем productId из URL
	vars := mux.Vars(r)
	productID, err := strconv.ParseUint(vars["productId"], 10, 32)
	if err != nil {
		http.Error(w, "Invalid product ID", http.StatusBadRequest)
		return
	}

	userID := uint(1)

	// Удаляем из БД и инвалидируем кэш
	err = h.db.RemoveFromCart(userID, uint(productID))
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	// Инвалидируем кэш корзины
	h.cache.Delete(fmt.Sprintf("cart_items:%d", userID))

	metrics.RecordCartOperation("remove")

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "success"})
}

func (h *Handlers) metricsHandler(w http.ResponseWriter, r *http.Request) {
	// Этот handler будет обрабатываться Prometheus middleware
	// Здесь просто заглушка, реальные метрики будут на /metrics через promhttp.Handler()
	w.WriteHeader(http.StatusOK)
	fmt.Fprint(w, "Metrics endpoint - use /metrics for Prometheus scraping")
}
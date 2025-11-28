package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"strconv"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/gorilla/mux"
	"github.com/gorilla/websocket"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

// Models
type User struct {
	ID        uint      `json:"id" gorm:"primaryKey"`
	Name      string    `json:"name"`
	Email     string    `json:"email" gorm:"unique"`
	CreatedAt time.Time `json:"created_at"`
}

type Product struct {
	ID          uint      `json:"id" gorm:"primaryKey"`
	Name        string    `json:"name"`
	Price       int       `json:"price"`
	Category    string    `json:"category"`
	Brand       string    `json:"brand"`
	Description string    `json:"description"`
	Stock       int       `json:"stock"`
	IsBestseller bool     `json:"is_bestseller"`
	IsFlashSale bool      `json:"is_flash_sale"`
	FlashPrice  *int      `json:"flash_price,omitempty"`
	CreatedAt   time.Time `json:"created_at"`
}

type Comment struct {
	ID        uint      `json:"id" gorm:"primaryKey"`
	UserID    uint      `json:"user_id"`
	ProductID uint      `json:"product_id"`
	Text      string    `json:"text"`
	Rating    int       `json:"rating"`
	User      User      `json:"user" gorm:"foreignKey:UserID"`
	Product   Product   `json:"product" gorm:"foreignKey:ProductID"`
	CreatedAt time.Time `json:"created_at"`
}

type CartItem struct {
	ID        uint    `json:"id" gorm:"primaryKey"`
	UserID    uint    `json:"user_id"`
	ProductID uint    `json:"product_id"`
	Quantity  int     `json:"quantity"`
	Product   Product `json:"product" gorm:"foreignKey:ProductID"`
	CreatedAt time.Time `json:"created_at"`
}

type FlashSale struct {
	ID        uint      `json:"id" gorm:"primaryKey"`
	ProductID uint      `json:"product_id"`
	SalePrice int       `json:"sale_price"`
	StartTime time.Time `json:"start_time"`
	EndTime   time.Time `json:"end_time"`
	Active    bool      `json:"active"`
	Product   Product   `json:"product" gorm:"foreignKey:ProductID"`
}

// WebSocket connection manager
type WSClient struct {
	conn   *websocket.Conn
	send   chan []byte
	userID uint
}

type WSHub struct {
	clients    map[*WSClient]bool
	broadcast  chan []byte
	register   chan *WSClient
	unregister chan *WSClient
}

func newWSHub() *WSHub {
	return &WSHub{
		clients:    make(map[*WSClient]bool),
		broadcast:  make(chan []byte),
		register:   make(chan *WSClient),
		unregister: make(chan *WSClient),
	}
}

func (h *WSHub) run() {
	for {
		select {
		case client := <-h.register:
			h.clients[client] = true
			log.Printf("WebSocket client connected (user: %d)", client.userID)

		case client := <-h.unregister:
			if _, ok := h.clients[client]; ok {
				delete(h.clients, client)
				close(client.send)
				log.Printf("WebSocket client disconnected (user: %d)", client.userID)
			}

		case message := <-h.broadcast:
			for client := range h.clients {
				select {
				case client.send <- message:
				default:
					delete(h.clients, client)
					close(client.send)
				}
			}
		}
	}
}

// Cache service with different strategies
type CacheService struct {
	redis *redis.Client
	db    *gorm.DB
	hub   *WSHub
}

func NewCacheService(redisClient *redis.Client, database *gorm.DB, hub *WSHub) *CacheService {
	return &CacheService{
		redis: redisClient,
		db:    database,
		hub:   hub,
	}
}

// TTL Caching for Bestsellers (1 hour)
func (cs *CacheService) GetBestsellers() ([]Product, error) {
	ctx := context.Background()
	cacheKey := "bestsellers"

	cached, err := cs.redis.Get(ctx, cacheKey).Result()
	if err == redis.Nil {
		// Cache miss - load from DB
		var products []Product
		err := cs.db.Where("is_bestseller = ?", true).Limit(4).Find(&products).Error
		if err != nil {
			return nil, err
		}

		// Cache for 1 hour (TTL)
		productsJSON, _ := json.Marshal(products)
		cs.redis.Set(ctx, cacheKey, productsJSON, time.Hour)

		log.Printf("Cache MISS for bestsellers (TTL: 1h)")
		return products, nil
	}

	var products []Product
	json.Unmarshal([]byte(cached), &products)
	log.Printf("Cache HIT for bestsellers")
	return products, nil
}

// Tag-based Caching for Recommendations
func (cs *CacheService) GetRecommendations(userID uint) ([]Product, error) {
	ctx := context.Background()
	cacheKey := fmt.Sprintf("recommendations:user:%d", userID)

	cached, err := cs.redis.Get(ctx, cacheKey).Result()
	if err == redis.Nil {
		// Get user's favorite categories/brands for recommendations
		var products []Product
		cs.db.Limit(3).Find(&products) // Simplified recommendation logic

		// Cache with tags for 1 hour
		productsJSON, _ := json.Marshal(products)
		cs.redis.Set(ctx, cacheKey, productsJSON, time.Hour)

		// Add tags for invalidation
		tagKey := fmt.Sprintf("tag:recommendations:user:%d", userID)
		cs.redis.SAdd(ctx, tagKey, cacheKey)
		cs.redis.Expire(ctx, tagKey, time.Hour)

		log.Printf("Cache MISS for recommendations (Tag-based)")
		return products, nil
	}

	var products []Product
	json.Unmarshal([]byte(cached), &products)
	log.Printf("Cache HIT for recommendations")
	return products, nil
}

// Event-based Invalidation for Flash Sales
func (cs *CacheService) GetFlashSales() ([]FlashSale, error) {
	ctx := context.Background()
	cacheKey := "flash_sales"

	cached, err := cs.redis.Get(ctx, cacheKey).Result()
	if err == redis.Nil {
		var flashSales []FlashSale
		err := cs.db.Preload("Product").Where("active = ? AND start_time <= ? AND end_time >= ?",
			true, time.Now(), time.Now()).Find(&flashSales).Error
		if err != nil {
			return nil, err
		}

		// Cache flash sales for 5 minutes (short TTL due to time sensitivity)
		salesJSON, _ := json.Marshal(flashSales)
		cs.redis.Set(ctx, cacheKey, salesJSON, 5*time.Minute)

		log.Printf("Cache MISS for flash sales (Event-based)")
		return flashSales, nil
	}

	var flashSales []FlashSale
	json.Unmarshal([]byte(cached), &flashSales)
	log.Printf("Cache HIT for flash sales")
	return flashSales, nil
}

// Event-based invalidation when flash sale is updated
func (cs *CacheService) InvalidateFlashSales() error {
	ctx := context.Background()
	cs.redis.Del(ctx, "flash_sales")

	// Notify all connected clients via WebSocket
	message := map[string]interface{}{
		"type": "flash_sale_update",
		"timestamp": time.Now(),
	}
	messageJSON, _ := json.Marshal(message)
	cs.hub.broadcast <- messageJSON

	log.Printf("Invalidated flash sales (Event-based)")
	return nil
}

// User profile caching with event-based invalidation
func (cs *CacheService) GetUserProfile(userID uint) (*User, error) {
	ctx := context.Background()
	cacheKey := fmt.Sprintf("user:profile:%d", userID)

	cached, err := cs.redis.Get(ctx, cacheKey).Result()
	if err == redis.Nil {
		var user User
		err := cs.db.First(&user, userID).Error
		if err != nil {
			return nil, err
		}

		userJSON, _ := json.Marshal(user)
		cs.redis.Set(ctx, cacheKey, userJSON, 30*time.Minute)

		log.Printf("Cache MISS for user profile %d", userID)
		return &user, nil
	}

	var user User
	json.Unmarshal([]byte(cached), &user)
	log.Printf("Cache HIT for user profile %d", userID)
	return &user, nil
}

// Event-based invalidation for user profile updates
func (cs *CacheService) UpdateUserProfile(user *User) error {
	ctx := context.Background()

	// Update in database
	err := cs.db.Save(user).Error
	if err != nil {
		return err
	}

	// Invalidate cache
	cacheKey := fmt.Sprintf("user:profile:%d", user.ID)
	cs.redis.Del(ctx, cacheKey)

	// Notify via WebSocket
	message := map[string]interface{}{
		"type": "profile_updated",
		"user_id": user.ID,
		"timestamp": time.Now(),
	}
	messageJSON, _ := json.Marshal(message)
	cs.hub.broadcast <- messageJSON

	log.Printf("Updated user profile %d (Event-based invalidation)", user.ID)
	return nil
}

// Top comments caching
func (cs *CacheService) GetTopComments() ([]Comment, error) {
	ctx := context.Background()
	cacheKey := "top_comments"

	cached, err := cs.redis.Get(ctx, cacheKey).Result()
	if err == redis.Nil {
		var comments []Comment
		err := cs.db.Preload("User").Preload("Product").Where("rating >= ?", 4).
			Order("rating DESC, created_at DESC").Limit(3).Find(&comments).Error
		if err != nil {
			return nil, err
		}

		commentsJSON, _ := json.Marshal(comments)
		cs.redis.Set(ctx, cacheKey, commentsJSON, 15*time.Minute)

		log.Printf("Cache MISS for top comments")
		return comments, nil
	}

	var comments []Comment
	json.Unmarshal([]byte(cached), &comments)
	log.Printf("Cache HIT for top comments")
	return comments, nil
}

// Cart management
func (cs *CacheService) GetCart(userID uint) ([]CartItem, error) {
	var cartItems []CartItem
	err := cs.db.Preload("Product").Where("user_id = ?", userID).Find(&cartItems).Error
	return cartItems, err
}

func (cs *CacheService) AddToCart(userID, productID uint, quantity int) error {
	// Check if item already exists
	var existing CartItem
	err := cs.db.Where("user_id = ? AND product_id = ?", userID, productID).First(&existing).Error

	if err == gorm.ErrRecordNotFound {
		// Create new cart item
		cartItem := CartItem{
			UserID:    userID,
			ProductID: productID,
			Quantity:  quantity,
		}
		return cs.db.Create(&cartItem).Error
	} else if err != nil {
		return err
	}

	// Update existing quantity
	existing.Quantity += quantity
	return cs.db.Save(&existing).Error
}

func (cs *CacheService) UpdateCartItem(userID, productID uint, quantity int) error {
	if quantity <= 0 {
		return cs.RemoveFromCart(userID, productID)
	}

	var cartItem CartItem
	err := cs.db.Where("user_id = ? AND product_id = ?", userID, productID).First(&cartItem).Error
	if err != nil {
		return err
	}

	cartItem.Quantity = quantity
	return cs.db.Save(&cartItem).Error
}

func (cs *CacheService) RemoveFromCart(userID, productID uint) error {
	return cs.db.Where("user_id = ? AND product_id = ?", userID, productID).Delete(&CartItem{}).Error
}

func (cs *CacheService) GetProduct(productID uint) (*Product, error) {
	var product Product
	err := cs.db.First(&product, productID).Error
	if err != nil {
		return nil, err
	}
	return &product, nil
}

// Server struct
type Server struct {
	cache *CacheService
	hub   *WSHub
}

// HTTP Handlers
func (s *Server) homeHandler(w http.ResponseWriter, r *http.Request) {
	http.ServeFile(w, r, "./static/index.html")
}

func (s *Server) getBestsellersHandler(w http.ResponseWriter, r *http.Request) {
	products, err := s.cache.GetBestsellers()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"products": products,
		"cache_strategy": "TTL (1 hour)",
	})
}

func (s *Server) getRecommendationsHandler(w http.ResponseWriter, r *http.Request) {
	userID := uint(1) // Simplified: get from session/auth
	products, err := s.cache.GetRecommendations(userID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"products": products,
		"cache_strategy": "Tag-based (1 hour)",
	})
}

func (s *Server) getFlashSalesHandler(w http.ResponseWriter, r *http.Request) {
	flashSales, err := s.cache.GetFlashSales()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"flash_sales": flashSales,
		"cache_strategy": "Event-based (5 min TTL)",
	})
}

func (s *Server) getUserProfileHandler(w http.ResponseWriter, r *http.Request) {
	userID := uint(1) // Simplified: get from session/auth
	user, err := s.cache.GetUserProfile(userID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"user": user,
		"cache_strategy": "Event-based invalidation",
	})
}

func (s *Server) updateUserProfileHandler(w http.ResponseWriter, r *http.Request) {
	var updateData struct {
		Name string `json:"name"`
	}

	err := json.NewDecoder(r.Body).Decode(&updateData)
	if err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	userID := uint(1) // Simplified: get from session/auth
	user, err := s.cache.GetUserProfile(userID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	user.Name = updateData.Name
	err = s.cache.UpdateUserProfile(user)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"user": user,
		"message": "Profile updated with event-based invalidation",
	})
}

func (s *Server) getTopCommentsHandler(w http.ResponseWriter, r *http.Request) {
	comments, err := s.cache.GetTopComments()
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"comments": comments,
		"cache_strategy": "TTL (15 minutes)",
	})
}

func (s *Server) getCartHandler(w http.ResponseWriter, r *http.Request) {
	userID := uint(1) // Simplified: get from session/auth
	cartItems, err := s.cache.GetCart(userID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(cartItems)
}

func (s *Server) addToCartHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	productID, err := strconv.ParseUint(vars["productId"], 10, 32)
	if err != nil {
		http.Error(w, "Invalid product ID", http.StatusBadRequest)
		return
	}

	var addData struct {
		Quantity int `json:"quantity"`
	}
	err = json.NewDecoder(r.Body).Decode(&addData)
	if err != nil {
		addData.Quantity = 1
	}

	userID := uint(1) // Simplified: get from session/auth
	err = s.cache.AddToCart(userID, uint(productID), addData.Quantity)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]bool{"success": true})
}

func (s *Server) updateCartHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	productID, err := strconv.ParseUint(vars["productId"], 10, 32)
	if err != nil {
		http.Error(w, "Invalid product ID", http.StatusBadRequest)
		return
	}

	var updateData struct {
		Quantity int `json:"quantity"`
	}
	err = json.NewDecoder(r.Body).Decode(&updateData)
	if err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	userID := uint(1) // Simplified: get from session/auth
	err = s.cache.UpdateCartItem(userID, uint(productID), updateData.Quantity)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]bool{"success": true})
}

func (s *Server) removeFromCartHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	productID, err := strconv.ParseUint(vars["productId"], 10, 32)
	if err != nil {
		http.Error(w, "Invalid product ID", http.StatusBadRequest)
		return
	}

	userID := uint(1) // Simplified: get from session/auth
	err = s.cache.RemoveFromCart(userID, uint(productID))
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]bool{"success": true})
}

func (s *Server) getProductHandler(w http.ResponseWriter, r *http.Request) {
	vars := mux.Vars(r)
	productID, err := strconv.ParseUint(vars["productId"], 10, 32)
	if err != nil {
		http.Error(w, "Invalid product ID", http.StatusBadRequest)
		return
	}

	product, err := s.cache.GetProduct(uint(productID))
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]interface{}{
		"success": true,
		"product": product,
	})
}

// WebSocket handler
var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		return true
	},
}

func (s *Server) wsHandler(w http.ResponseWriter, r *http.Request) {
	conn, err := upgrader.Upgrade(w, r, nil)
	if err != nil {
		log.Printf("WebSocket upgrade error: %v", err)
		return
	}

	userID := uint(1) // Simplified: get from session/auth
	client := &WSClient{
		conn:   conn,
		send:   make(chan []byte, 256),
		userID: userID,
	}

	s.hub.register <- client

	go client.writePump()
	go client.readPump(s.hub)
}

func (c *WSClient) readPump(hub *WSHub) {
	defer func() {
		hub.unregister <- c
		c.conn.Close()
	}()

	for {
		_, _, err := c.conn.ReadMessage()
		if err != nil {
			break
		}
	}
}

func (c *WSClient) writePump() {
	defer c.conn.Close()

	for {
		select {
		case message, ok := <-c.send:
			if !ok {
				c.conn.WriteMessage(websocket.CloseMessage, []byte{})
				return
			}

			c.conn.WriteMessage(websocket.TextMessage, message)
		}
	}
}

// Cache invalidation handlers
func (s *Server) invalidateBestsellersHandler(w http.ResponseWriter, r *http.Request) {
	ctx := context.Background()

	// Очищаем TTL кэш бестселлеров
	err := s.cache.rdb.Del(ctx, "bestsellers").Err()
	if err != nil {
		http.Error(w, "Failed to invalidate cache", http.StatusInternalServerError)
		return
	}

	// Отправляем WebSocket уведомление
	s.hub.broadcast <- []byte(`{"type":"cache_invalidated","cache":"bestsellers"}`)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "success", "message": "Bestsellers cache invalidated"})
}

func (s *Server) invalidateRecommendationsHandler(w http.ResponseWriter, r *http.Request) {
	ctx := context.Background()

	// Очищаем тегированный кэш рекомендаций для всех пользователей
	pattern := "recommendations:user:*"
	keys, err := s.cache.rdb.Keys(ctx, pattern).Result()
	if err != nil {
		http.Error(w, "Failed to find cache keys", http.StatusInternalServerError)
		return
	}

	if len(keys) > 0 {
		err = s.cache.rdb.Del(ctx, keys...).Err()
		if err != nil {
			http.Error(w, "Failed to invalidate cache", http.StatusInternalServerError)
			return
		}
	}

	// Очищаем теги
	s.cache.rdb.Del(ctx, "tags:recommendations")

	// Отправляем WebSocket уведомление
	s.hub.broadcast <- []byte(`{"type":"cache_invalidated","cache":"recommendations"}`)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "success", "message": "Recommendations cache invalidated"})
}

func (s *Server) invalidateFlashSalesHandler(w http.ResponseWriter, r *http.Request) {
	ctx := context.Background()

	// Очищаем кэш flash sales
	err := s.cache.rdb.Del(ctx, "flash_sales").Err()
	if err != nil {
		http.Error(w, "Failed to invalidate cache", http.StatusInternalServerError)
		return
	}

	// Отправляем WebSocket уведомление о событии
	s.hub.broadcast <- []byte(`{"type":"flash_sales_updated"}`)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "success", "message": "Flash sales cache invalidated"})
}

func (s *Server) invalidateUserProfileHandler(w http.ResponseWriter, r *http.Request) {
	ctx := context.Background()
	userID := uint(1) // В реальном приложении получать из сессии

	// Очищаем кэш профиля пользователя
	cacheKey := fmt.Sprintf("user_profile:%d", userID)
	err := s.cache.rdb.Del(ctx, cacheKey).Err()
	if err != nil {
		http.Error(w, "Failed to invalidate cache", http.StatusInternalServerError)
		return
	}

	// Отправляем WebSocket уведомление о событии
	message := fmt.Sprintf(`{"type":"profile_updated","user_id":%d}`, userID)
	s.hub.broadcast <- []byte(message)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "success", "message": "User profile cache invalidated"})
}

func (s *Server) invalidateAllCachesHandler(w http.ResponseWriter, r *http.Request) {
	ctx := context.Background()

	// Очищаем все типы кэшей
	patterns := []string{
		"bestsellers",
		"flash_sales",
		"recommendations:user:*",
		"user_profile:*",
		"tags:*",
		"top_comments",
	}

	for _, pattern := range patterns {
		if pattern == "bestsellers" || pattern == "flash_sales" || pattern == "top_comments" {
			s.cache.rdb.Del(ctx, pattern)
		} else {
			keys, err := s.cache.rdb.Keys(ctx, pattern).Result()
			if err == nil && len(keys) > 0 {
				s.cache.rdb.Del(ctx, keys...)
			}
		}
	}

	// Отправляем WebSocket уведомление
	s.hub.broadcast <- []byte(`{"type":"all_caches_invalidated"}`)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "success", "message": "All caches invalidated"})
}

func (s *Server) getCacheStatusHandler(w http.ResponseWriter, r *http.Request) {
	ctx := context.Background()

	// Проверяем статус различных кэшей
	status := map[string]interface{}{
		"bestsellers": s.cache.rdb.Exists(ctx, "bestsellers").Val() > 0,
		"flash_sales": s.cache.rdb.Exists(ctx, "flash_sales").Val() > 0,
		"top_comments": s.cache.rdb.Exists(ctx, "top_comments").Val() > 0,
	}

	// Проверяем рекомендации пользователей
	recKeys, _ := s.cache.rdb.Keys(ctx, "recommendations:user:*").Result()
	status["recommendations_users"] = len(recKeys)

	// Проверяем профили пользователей
	profileKeys, _ := s.cache.rdb.Keys(ctx, "user_profile:*").Result()
	status["user_profiles"] = len(profileKeys)

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(status)
}

func main() {
	// Database connection
	dsn := "host=postgres user=demo_user password=demo_pass dbname=ecommerce_db port=5432 sslmode=disable"
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		log.Fatal("Failed to connect to database:", err)
	}

	// Auto migration
	db.AutoMigrate(&User{}, &Product{}, &Comment{}, &CartItem{}, &FlashSale{})

	// Redis connection
	rdb := redis.NewClient(&redis.Options{
		Addr: "redis:6379",
	})

	// WebSocket hub
	hub := newWSHub()
	go hub.run()

	// Cache service
	cache := NewCacheService(rdb, db, hub)

	// Seed data
	seedData(db)

	// Server
	server := &Server{cache: cache, hub: hub}

	// Routes
	r := mux.NewRouter()

	// API routes
	api := r.PathPrefix("/api").Subrouter()
	api.HandleFunc("/bestsellers", server.getBestsellersHandler).Methods("GET")
	api.HandleFunc("/recommendations", server.getRecommendationsHandler).Methods("GET")
	api.HandleFunc("/flash-sales", server.getFlashSalesHandler).Methods("GET")
	api.HandleFunc("/user/profile", server.getUserProfileHandler).Methods("GET")
	api.HandleFunc("/user/profile", server.updateUserProfileHandler).Methods("PUT")
	api.HandleFunc("/comments/top", server.getTopCommentsHandler).Methods("GET")
	api.HandleFunc("/cart", server.getCartHandler).Methods("GET")
	api.HandleFunc("/cart/add/{productId:[0-9]+}", server.addToCartHandler).Methods("POST")
	api.HandleFunc("/cart/update/{productId:[0-9]+}", server.updateCartHandler).Methods("PUT")
	api.HandleFunc("/cart/remove/{productId:[0-9]+}", server.removeFromCartHandler).Methods("DELETE")
	api.HandleFunc("/products/{productId:[0-9]+}", server.getProductHandler).Methods("GET")

	// Cache invalidation endpoints
	api.HandleFunc("/cache/status", server.getCacheStatusHandler).Methods("GET")
	api.HandleFunc("/cache/invalidate/bestsellers", server.invalidateBestsellersHandler).Methods("POST")
	api.HandleFunc("/cache/invalidate/recommendations", server.invalidateRecommendationsHandler).Methods("POST")
	api.HandleFunc("/cache/invalidate/flash-sales", server.invalidateFlashSalesHandler).Methods("POST")
	api.HandleFunc("/cache/invalidate/profile", server.invalidateUserProfileHandler).Methods("POST")
	api.HandleFunc("/cache/invalidate/all", server.invalidateAllCachesHandler).Methods("POST")

	// WebSocket
	r.HandleFunc("/ws", server.wsHandler)

	// Static files
	r.HandleFunc("/", server.homeHandler)
	r.PathPrefix("/static/").Handler(http.StripPrefix("/static/", http.FileServer(http.Dir("./static/"))))

	fmt.Println("🚀 ТЕХНОМИР Server starting on :8080")
	fmt.Println("📊 Cache strategies implemented:")
	fmt.Println("   - TTL (1h): Bestsellers, Recommendations")
	fmt.Println("   - Tag-based: Recommendations per user")
	fmt.Println("   - Event-based: Flash Sales, User Profile")
	fmt.Println("   - WebSockets: Real-time updates")
	log.Fatal(http.ListenAndServe(":8080", r))
}

func seedData(db *gorm.DB) {
	// Users
	users := []User{
		{Name: "Дмитрий Иванов", Email: "dmitry@example.com"},
		{Name: "Анна Петрова", Email: "anna@example.com"},
		{Name: "Сергей Козлов", Email: "sergey@example.com"},
	}
	for _, user := range users {
		db.FirstOrCreate(&user, User{Email: user.Email})
	}

	// Products
	products := []Product{
		{Name: "iPhone 15 Pro", Price: 120000, Category: "smartphones", Brand: "Apple", Description: "Latest iPhone", Stock: 50, IsBestseller: true},
		{Name: "MacBook Pro 16", Price: 250000, Category: "laptops", Brand: "Apple", Description: "Professional laptop", Stock: 20, IsBestseller: true},
		{Name: "AirPods Pro 2", Price: 28000, Category: "accessories", Brand: "Apple", Description: "Wireless earphones", Stock: 100, IsBestseller: true},
		{Name: "Samsung Galaxy S24", Price: 80000, Category: "smartphones", Brand: "Samsung", Description: "Android flagship", Stock: 30, IsBestseller: true},
		{Name: "PlayStation 5", Price: 55000, Category: "gaming", Brand: "Sony", Description: "Next-gen console", Stock: 15, IsFlashSale: true},
		{Name: "Xbox Series X", Price: 50000, Category: "gaming", Brand: "Microsoft", Description: "Gaming console", Stock: 25},
	}
	for _, product := range products {
		db.FirstOrCreate(&product, Product{Name: product.Name})
	}

	// Flash Sales
	flashSales := []FlashSale{
		{ProductID: 5, SalePrice: 45000, StartTime: time.Now(), EndTime: time.Now().Add(24 * time.Hour), Active: true},
	}
	for _, sale := range flashSales {
		db.FirstOrCreate(&sale, FlashSale{ProductID: sale.ProductID})
	}

	// Comments
	comments := []Comment{
		{UserID: 1, ProductID: 1, Text: "Отличный телефон!", Rating: 5},
		{UserID: 2, ProductID: 2, Text: "Мощный ноутбук для работы", Rating: 5},
		{UserID: 3, ProductID: 3, Text: "Хорошее качество звука", Rating: 4},
	}
	for _, comment := range comments {
		db.FirstOrCreate(&comment, Comment{UserID: comment.UserID, ProductID: comment.ProductID})
	}
}
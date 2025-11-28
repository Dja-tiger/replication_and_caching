package cache

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"sync"
	"time"

	"github.com/go-redis/redis/v8"
	"ecommerce-backend/metrics"
)

type CacheStrategy string

const (
	CacheAside    CacheStrategy = "cache-aside"    // Приложение управляет кэшем
	WriteThrough  CacheStrategy = "write-through"  // Запись в БД и кэш одновременно
	RefreshAhead  CacheStrategy = "refresh-ahead"  // Проактивное обновление
)

type CacheService struct {
	rdb         *redis.Client
	ctx         context.Context
	mu          sync.RWMutex
	refreshers  map[string]*time.Ticker // для Refresh-Ahead
}

type CacheOptions struct {
	TTL      time.Duration
	Strategy CacheStrategy
	Tags     []string
	RefreshFunc func() (interface{}, error) // для Refresh-Ahead
}

func NewCacheService(addr, password string, db int) *CacheService {
	rdb := redis.NewClient(&redis.Options{
		Addr:     addr,
		Password: password,
		DB:       db,
	})

	ctx := context.Background()

	// Test connection
	_, err := rdb.Ping(ctx).Result()
	if err != nil {
		log.Printf("Failed to connect to Redis: %v", err)
	}

	return &CacheService{
		rdb:        rdb,
		ctx:        ctx,
		refreshers: make(map[string]*time.Ticker),
	}
}

// Cache-Aside паттерн: приложение само управляет кэшем
func (c *CacheService) GetWithCacheAside(key string, dest interface{}, fetchFunc func() (interface{}, error), ttl time.Duration) error {
	start := time.Now()

	// Пытаемся получить из кэша
	val, err := c.rdb.Get(c.ctx, key).Result()
	if err == redis.Nil {
		// Cache miss - загружаем из источника
		metrics.RecordCacheMiss("cache-aside")

		data, err := fetchFunc()
		if err != nil {
			return err
		}

		// Сохраняем в кэш
		jsonData, err := json.Marshal(data)
		if err != nil {
			return err
		}

		c.rdb.Set(c.ctx, key, jsonData, ttl)

		// Копируем результат в dest
		return json.Unmarshal(jsonData, dest)
	} else if err != nil {
		return err
	}

	// Cache hit
	metrics.RecordCacheHit("cache-aside")
	log.Printf("Cache hit for key: %s, duration: %v", key, time.Since(start))

	return json.Unmarshal([]byte(val), dest)
}

// Write-Through паттерн: запись в БД и кэш одновременно
func (c *CacheService) SetWithWriteThrough(key string, value interface{}, writeFunc func(interface{}) error, ttl time.Duration) error {
	// Сначала записываем в БД
	if err := writeFunc(value); err != nil {
		return err
	}

	// Затем в кэш
	data, err := json.Marshal(value)
	if err != nil {
		return err
	}

	return c.rdb.Set(c.ctx, key, data, ttl).Err()
}

// Refresh-Ahead паттерн: проактивное обновление кэша
func (c *CacheService) SetWithRefreshAhead(key string, refreshFunc func() (interface{}, error), ttl time.Duration, refreshBefore time.Duration) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	// Останавливаем предыдущий refresher если есть
	if ticker, exists := c.refreshers[key]; exists {
		ticker.Stop()
	}

	// Изначально загружаем данные
	data, err := refreshFunc()
	if err != nil {
		return err
	}

	jsonData, err := json.Marshal(data)
	if err != nil {
		return err
	}

	if err := c.rdb.Set(c.ctx, key, jsonData, ttl).Err(); err != nil {
		return err
	}

	// Запускаем периодическое обновление
	refreshInterval := ttl - refreshBefore
	if refreshInterval > 0 {
		ticker := time.NewTicker(refreshInterval)
		c.refreshers[key] = ticker

		go func() {
			for range ticker.C {
				if newData, err := refreshFunc(); err == nil {
					if newJsonData, err := json.Marshal(newData); err == nil {
						c.rdb.Set(c.ctx, key, newJsonData, ttl)
						log.Printf("Proactively refreshed cache for key: %s", key)
					}
				}
			}
		}()
	}

	return nil
}

// Базовые методы
func (c *CacheService) Set(key string, value interface{}, expiration time.Duration) error {
	data, err := json.Marshal(value)
	if err != nil {
		return err
	}
	return c.rdb.Set(c.ctx, key, data, expiration).Err()
}

func (c *CacheService) Get(key string, dest interface{}) error {
	val, err := c.rdb.Get(c.ctx, key).Result()
	if err != nil {
		return err
	}
	return json.Unmarshal([]byte(val), dest)
}

func (c *CacheService) Delete(key string) error {
	return c.rdb.Del(c.ctx, key).Err()
}

func (c *CacheService) DeletePattern(pattern string) error {
	keys, err := c.rdb.Keys(c.ctx, pattern).Result()
	if err != nil {
		return err
	}

	if len(keys) > 0 {
		return c.rdb.Del(c.ctx, keys...).Err()
	}
	return nil
}

func (c *CacheService) SetWithTags(key string, value interface{}, expiration time.Duration, tags []string) error {
	// Set main cache
	if err := c.Set(key, value, expiration); err != nil {
		return err
	}

	// Set tag associations
	for _, tag := range tags {
		tagKey := fmt.Sprintf("tag:%s", tag)
		if err := c.rdb.SAdd(c.ctx, tagKey, key).Err(); err != nil {
			return err
		}
		if expiration > 0 {
			c.rdb.Expire(c.ctx, tagKey, expiration)
		}
	}

	return nil
}

func (c *CacheService) InvalidateByTag(tag string) error {
	tagKey := fmt.Sprintf("tag:%s", tag)

	// Get all keys associated with this tag
	keys, err := c.rdb.SMembers(c.ctx, tagKey).Result()
	if err != nil {
		return err
	}

	// Delete all associated keys
	if len(keys) > 0 {
		if err := c.rdb.Del(c.ctx, keys...).Err(); err != nil {
			return err
		}
	}

	// Delete the tag set itself
	return c.rdb.Del(c.ctx, tagKey).Err()
}

func (c *CacheService) InvalidateBestsellers() error {
	return c.Delete("bestsellers")
}

func (c *CacheService) InvalidateRecommendations() error {
	return c.DeletePattern("recommendations:*")
}

func (c *CacheService) InvalidateFlashSales() error {
	return c.Delete("flash_sales")
}

func (c *CacheService) InvalidateProfile(userID uint) error {
	return c.Delete(fmt.Sprintf("profile:%d", userID))
}

func (c *CacheService) InvalidateComments() error {
	return c.Delete("top_comments")
}

func (c *CacheService) InvalidateAll() error {
	return c.rdb.FlushDB(c.ctx).Err()
}

func (c *CacheService) GetCacheStatus() map[string]interface{} {
	status := make(map[string]interface{})

	keys := []string{
		"bestsellers",
		"flash_sales",
		"top_comments",
	}

	for _, key := range keys {
		ttl := c.rdb.TTL(c.ctx, key).Val()
		exists := c.rdb.Exists(c.ctx, key).Val()

		status[key] = map[string]interface{}{
			"exists": exists == 1,
			"ttl":    ttl.Seconds(),
		}
	}

	// Check recommendations pattern
	recKeys, _ := c.rdb.Keys(c.ctx, "recommendations:*").Result()
	status["recommendations"] = map[string]interface{}{
		"count": len(recKeys),
		"keys":  recKeys,
	}

	return status
}

// Метод для получения рекомендаций с Cache-Aside и персонализацией
func (c *CacheService) GetRecommendationsWithCacheAside(userID uint, fetchFunc func(uint) (interface{}, error)) (interface{}, error) {
	key := fmt.Sprintf("recommendations:%d", userID)
	ttl := c.GetTTLForDataType("recommendations")

	var result interface{}
	err := c.GetWithCacheAside(key, &result, func() (interface{}, error) {
		return fetchFunc(userID)
	}, ttl)

	return result, err
}

// Метод для бестселлеров с Refresh-Ahead
func (c *CacheService) GetBestsellersWithRefreshAhead(fetchFunc func() (interface{}, error)) (interface{}, error) {
	key := "bestsellers"
	ttl := c.GetTTLForDataType("bestsellers")
	refreshBefore := 10 * time.Minute // Обновляем за 10 минут до истечения

	// Проверяем, есть ли данные в кэше
	var result interface{}
	err := c.Get(key, &result)
	if err == nil {
		return result, nil
	}

	// Если данных нет, устанавливаем Refresh-Ahead
	err = c.SetWithRefreshAhead(key, fetchFunc, ttl, refreshBefore)
	if err != nil {
		return nil, err
	}

	// Возвращаем свежие данные
	err = c.Get(key, &result)
	return result, err
}

func (c *CacheService) Close() error {
	// Останавливаем все refreshers
	c.mu.Lock()
	for _, ticker := range c.refreshers {
		ticker.Stop()
	}
	c.refreshers = make(map[string]*time.Ticker)
	c.mu.Unlock()

	return c.rdb.Close()
}

// TTL стратегии по типам данных (из лекции)
func (c *CacheService) GetTTLForDataType(dataType string) time.Duration {
	switch dataType {
	case "bestsellers":
		return 1 * time.Hour    // Стабильные данные
	case "recommendations":
		return 1 * time.Hour    // Персонализированные данные
	case "flash_sales":
		return 5 * time.Minute  // Динамические данные
	case "user_profile":
		return 30 * time.Minute // Пользовательские данные
	case "top_comments":
		return 2 * time.Hour    // Редко изменяемые данные
	case "cart":
		return 10 * time.Minute // Часто изменяемые данные
	default:
		return 5 * time.Minute  // По умолчанию
	}
}

// Специальные методы для разных стратегий инвалидации
func (c *CacheService) InvalidateWithStrategy(cacheType string) error {
	metrics.RecordCacheInvalidation(cacheType)

	switch cacheType {
	case "bestsellers":
		// TTL инвалидация - просто удаляем
		return c.Delete("bestsellers")
	case "recommendations":
		// Tag инвалидация - удаляем по паттерну
		return c.DeletePattern("recommendations:*")
	case "flash-sales":
		// Event инвалидация - удаляем и уведомляем
		if err := c.Delete("flash_sales"); err != nil {
			return err
		}
		// Можно добавить публикацию события для WebSocket
		return c.rdb.Publish(c.ctx, "cache_invalidated", "flash_sales").Err()
	case "profile":
		// Event инвалидация для профилей
		return c.DeletePattern("profile:*")
	default:
		return c.Delete(cacheType)
	}
}
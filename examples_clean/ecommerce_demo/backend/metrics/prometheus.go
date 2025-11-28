package metrics

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

var (
	// HTTP Metrics
	HTTPRequestsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "http_requests_total",
			Help: "Total number of HTTP requests",
		},
		[]string{"method", "endpoint", "status_code"},
	)

	HTTPRequestDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "http_request_duration_seconds",
			Help:    "Duration of HTTP requests in seconds",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"method", "endpoint"},
	)

	// Cache Metrics
	CacheHitsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "cache_hits_total",
			Help: "Total number of cache hits",
		},
		[]string{"cache_type"},
	)

	CacheMissesTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "cache_misses_total",
			Help: "Total number of cache misses",
		},
		[]string{"cache_type"},
	)

	CacheInvalidationsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "cache_invalidations_total",
			Help: "Total number of cache invalidations",
		},
		[]string{"cache_type"},
	)

	// Database Metrics
	DatabaseQueriesTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "database_queries_total",
			Help: "Total number of database queries",
		},
		[]string{"operation", "table"},
	)

	DatabaseQueryDuration = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "database_query_duration_seconds",
			Help:    "Duration of database queries in seconds",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"operation", "table"},
	)

	// WebSocket Metrics
	WebSocketConnectionsActive = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "websocket_connections_active",
			Help: "Number of active WebSocket connections",
		},
	)

	WebSocketMessagesTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "websocket_messages_total",
			Help: "Total number of WebSocket messages",
		},
		[]string{"direction", "message_type"},
	)

	// Business Metrics
	ProductViewsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "product_views_total",
			Help: "Total number of product views",
		},
		[]string{"product_id"},
	)

	CartOperationsTotal = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "cart_operations_total",
			Help: "Total number of cart operations",
		},
		[]string{"operation"},
	)

	ActiveUsers = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "active_users",
			Help: "Number of active users",
		},
	)

	// Application Metrics
	ApplicationStartTime = promauto.NewGauge(
		prometheus.GaugeOpts{
			Name: "application_start_time_seconds",
			Help: "Time when the application started",
		},
	)

	ApplicationInfo = promauto.NewGaugeVec(
		prometheus.GaugeOpts{
			Name: "application_info",
			Help: "Application information",
		},
		[]string{"version", "build_date"},
	)
)

func init() {
	// Set application start time
	ApplicationStartTime.SetToCurrentTime()

	// Set application info
	ApplicationInfo.WithLabelValues("1.0.0", "2024-01-01").Set(1)
}

// Helper functions for common metrics
func RecordHTTPRequest(method, endpoint, statusCode string, duration float64) {
	HTTPRequestsTotal.WithLabelValues(method, endpoint, statusCode).Inc()
	HTTPRequestDuration.WithLabelValues(method, endpoint).Observe(duration)
}

func RecordCacheHit(cacheType string) {
	CacheHitsTotal.WithLabelValues(cacheType).Inc()
}

func RecordCacheMiss(cacheType string) {
	CacheMissesTotal.WithLabelValues(cacheType).Inc()
}

func RecordCacheInvalidation(cacheType string) {
	CacheInvalidationsTotal.WithLabelValues(cacheType).Inc()
}

func RecordDatabaseQuery(operation, table string, duration float64) {
	DatabaseQueriesTotal.WithLabelValues(operation, table).Inc()
	DatabaseQueryDuration.WithLabelValues(operation, table).Observe(duration)
}

func RecordWebSocketMessage(direction, messageType string) {
	WebSocketMessagesTotal.WithLabelValues(direction, messageType).Inc()
}

func SetActiveWebSocketConnections(count int) {
	WebSocketConnectionsActive.Set(float64(count))
}

func RecordProductView(productID string) {
	ProductViewsTotal.WithLabelValues(productID).Inc()
}

func RecordCartOperation(operation string) {
	CartOperationsTotal.WithLabelValues(operation).Inc()
}

func SetActiveUsers(count int) {
	ActiveUsers.Set(float64(count))
}
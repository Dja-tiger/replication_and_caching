@Configuration
@EnableCaching
public class CacheConfig {

    @Bean
    public CacheManager cacheManager() {
        return new JCacheCacheManager();
    }

    @Bean
    public javax.cache.CacheManager ehCacheManager() {
        CachingProvider provider = Caching.getCachingProvider();
        javax.cache.CacheManager manager = provider.getCacheManager();

        // Конфигурация для каталога Техномира
        Configuration<Long, Product> config = new MutableConfiguration<>()
            .setExpiryPolicyFactory(CreatedExpiryPolicy
                .factoryOf(Duration.FIVE_MINUTES))
            .setReadThrough(true)
            .setCacheLoaderFactory(() -> new ProductCacheLoader())
            .setWriteThrough(true)
            .setCacheWriterFactory(() -> new ProductCacheWriter());

        manager.createCache("products", config);
        return manager;
    }
}
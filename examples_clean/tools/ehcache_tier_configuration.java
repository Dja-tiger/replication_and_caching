// Техномир: трёхуровневое кэширование
CacheManager cacheManager = CacheManagerBuilder.newCacheManagerBuilder()
    .withCache("products",
        CacheConfigurationBuilder.newCacheConfigurationBuilder(
            Long.class, Product.class,
            ResourcePoolsBuilder.newResourcePoolsBuilder()
                .heap(1000, EntryUnit.ENTRIES)       // L1: JVM heap
                .offheap(10, MemoryUnit.MB)          // L2: Direct memory
                .disk(100, MemoryUnit.MB, true)      // L3: Persistent
        )
        .withExpiry(ExpiryPolicyBuilder.timeToLiveExpiration(
            Duration.ofMinutes(30)
        ))
    )
    .build(true);

// Преимущество: автоматическое перемещение между уровнями
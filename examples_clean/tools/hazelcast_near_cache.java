// Техномир: Near Cache для минимизации сетевых вызовов
NearCacheConfig nearCacheConfig = new NearCacheConfig()
    .setName("products")
    .setMaxSize(5000)  // Максимум записей в локальном кэше
    .setTimeToLiveSeconds(300)
    .setInvalidateOnChange(true)  // Инвалидация при изменении
    .setEvictionConfig(new EvictionConfig()
        .setEvictionPolicy(EvictionPolicy.LRU)
        .setMaxSizePolicy(MaxSizePolicy.ENTRY_COUNT));

ClientConfig clientConfig = new ClientConfig();
clientConfig.addNearCacheConfig(nearCacheConfig);

HazelcastInstance client = HazelcastClient.newHazelcastClient(clientConfig);
IMap<Long, Product> products = client.getMap("products");

// Первый запрос - из кластера
Product p1 = products.get(123L);  // ~10ms

// Последующие - из Near Cache
Product p2 = products.get(123L);  // ~0.1ms
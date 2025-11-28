func WarmCacheOnFailover(ctx context.Context) {
    // Получаем критические ключи
    hotKeys := identifyHotKeys()

    // Параллельный прогрев
    var wg sync.WaitGroup
    for _, key := range hotKeys {
        wg.Add(1)
        go func(k string) {
            defer wg.Done()
            data := db.Query(k)
            cache.Set(k, data, ttl)
        }(key)
    }
    wg.Wait()
}
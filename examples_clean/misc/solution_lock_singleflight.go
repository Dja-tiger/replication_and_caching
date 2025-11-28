// Go: используем singleflight
var group singleflight.Group

func GetProduct(id string) (*Product, error) {
    key := fmt.Sprintf("product:%s", id)

    // Только один поток выполнит запрос
    val, err, _ := group.Do(key, func() (interface{}, error) {
        // Проверяем кэш ещё раз
        if cached := cache.Get(key); cached != nil {
            return cached, nil
        }
        // Идём в базу
        product := db.GetProduct(id)
        cache.Set(key, product, ttl)
        return product, nil
    })
    return val.(*Product), err
}
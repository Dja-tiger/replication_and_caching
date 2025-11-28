// Техномир: реактивная обработка изменений кэша
public class CacheEventProcessor {

    public void setupListeners(HazelcastInstance hz) {
        IMap<Long, Product> products = hz.getMap("products");

        // Слушатель изменений
        products.addEntryListener(new EntryAdapter<Long, Product>() {
            @Override
            public void entryAdded(EntryEvent<Long, Product> event) {
                // Новый товар добавлен
                indexService.indexProduct(event.getValue());
                notificationService.notifyNewProduct(event.getValue());
            }

            @Override
            public void entryUpdated(EntryEvent<Long, Product> event) {
                // Цена изменилась - пересчитать скидки
                if (event.getValue().getPrice() !=
                    event.getOldValue().getPrice()) {
                    discountService.recalculate(event.getKey());
                }
            }
        }, true);  // includeValue = true
    }
}

// Событие распространяется на все узлы кластера
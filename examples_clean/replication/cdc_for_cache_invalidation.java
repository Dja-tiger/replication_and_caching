@EventListener
public void handleChangeEvent(DebeziumEvent event) {
    String table = event.getTable();
    String operation = event.getOp();

    switch (operation) {
        case "u": // UPDATE
        case "d": // DELETE
            String key = extractKey(event);
            cache.delete("cache:" + table + ":" + key);

            // Публикуем для других нод
            redis.publish("invalidation:" + table, key);
            break;
    }
}
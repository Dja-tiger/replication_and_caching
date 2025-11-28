# Write-Through с инвалидацией (продолжение)

# 2. Инвалидируем только затронутые кэши
        invalidation_keys = calculate_invalidation_keys(
            product, changes
        )

        for key in invalidation_keys:
            cache.delete(key)

        # 3. Асинхронное обновление зависимых кэшей
        queue.publish("cache.refresh", {
            "product_id": product_id,
            "changed_fields": list(changes.keys())
        })
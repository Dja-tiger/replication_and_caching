# Централизованная инвалидация (продолжение)

def on_product_update(self, event):
        product_id = event['product_id']
        changes = event['changes']

        # Базовые ключи товара
        self.invalidate_keys([
            f"product:{product_id}",
            f"product:{product_id}:details"
        ])

        # Условная инвалидация
        if 'category_id' in changes:
            self.invalidate_category_caches(
                changes['old_category'], changes['new_category']
            )
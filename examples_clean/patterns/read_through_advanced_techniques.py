# Read-Through: продвинутые техники

# Техномир: Read-Through с предзагрузкой
class PredictiveReadThrough:
    def __init__(self, cache, db, ml_model):
        self.cache = cache
        self.db = db
        self.ml_model = ml_model

    def get(self, key, context=None):
        """Чтение с предсказанием следующих запросов"""

        # Обычное Read-Through
        data = self._read_through(key)

        # Предсказываем, что понадобится дальше
        if context:
            predictions = self.ml_model.predict_next(
                key, context
            )

            # Асинхронно подгружаем предсказанное
            for predicted_key, probability in predictions:
                if probability > 0.7:
                    self._async_prefetch(predicted_key)

        return data

    def _async_prefetch(self, key):
        """Фоновая предзагрузка"""
        threading.Thread(
            target=lambda: self._read_through(key)
        ).start()
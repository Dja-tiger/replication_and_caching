# Кейс: персонализация Техномир (1/2)

# Персональные рекомендации с кэшированием
class PersonalizationService:
    def get_recommendations(self, user_id):
        # L1: персональный кэш пользователя
        personal = redis.get(f"reco:user:{user_id}")
        if personal:
            return personal

        # L2: сегментный кэш
        segment = self.get_user_segment(user_id)
        segment_reco = redis.get(f"reco:seg:{segment}")
        if segment_reco:
            # Персонализируем общие рекомендации
            return self.personalize(segment_reco, user_id)
# Кейс: персонализация Техномир (2/2)

# L3: холодный старт из реплики
        replica = self.get_read_replica()
        recommendations = replica.query("""
            SELECT p.* FROM products p
            JOIN user_interests ui ON ...
            WHERE ui.user_id = ?
        """, user_id)

        # Кэшируем на разных уровнях
        redis.setex(f"reco:user:{user_id}", 300,
                   recommendations)
        redis.setex(f"reco:seg:{segment}", 600,
                   recommendations)
        return recommendations
// Техномир: проблема false sharing в многопоточном кэше
public class CacheStats {
    // ❌ Плохо: переменные в одной cache line
    volatile long hits;     // Thread 1 обновляет
    volatile long misses;   // Thread 2 обновляет
    // При обновлении одной - инвалидируется вся cache line

    // ✅ Хорошо: padding для разных cache lines
    @Contended
    volatile long paddedHits;

    @Contended
    volatile long paddedMisses;
}

// Или ручной padding
class PaddedCacheStats {
    volatile long hits;
    long p1, p2, p3, p4, p5, p6, p7;  // 64 байта padding
    volatile long misses;
    long p8, p9, p10, p11, p12, p13, p14;
}

// Результат: 3x улучшение производительности при высокой конкуренции
#!/usr/bin/env python3
"""
LFU (Least Frequently Used) Cache - полная реализация

LFU удаляет наименее часто используемые элементы.
При одинаковой частоте использует LRU для выбора жертвы.
"""

from collections import OrderedDict, defaultdict
import heapq
import time


class LFUCache:
    """LFU кэш с O(1) операциями"""

    def __init__(self, capacity):
        """
        Инициализация LFU кэша

        Args:
            capacity: Максимальный размер кэша
        """
        if capacity <= 0:
            raise ValueError("Capacity must be positive")

        self.capacity = capacity
        self.min_freq = 0

        # Основное хранилище: key -> (value, freq)
        self.key_to_val_freq = {}

        # Частоты: freq -> OrderedDict of keys
        self.freq_to_keys = defaultdict(OrderedDict)

        # Статистика
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def _update_freq(self, key, value=None):
        """Обновить частоту использования ключа"""
        if key in self.key_to_val_freq:
            # Существующий ключ
            old_value, old_freq = self.key_to_val_freq[key]
            new_freq = old_freq + 1

            # Удаляем из старой частоты
            del self.freq_to_keys[old_freq][key]
            if len(self.freq_to_keys[old_freq]) == 0:
                del self.freq_to_keys[old_freq]
                # Обновляем минимальную частоту если нужно
                if self.min_freq == old_freq:
                    self.min_freq += 1

            # Обновляем значение если передано
            final_value = value if value is not None else old_value

            # Добавляем в новую частоту
            self.key_to_val_freq[key] = (final_value, new_freq)
            self.freq_to_keys[new_freq][key] = None
        else:
            # Новый ключ
            self.key_to_val_freq[key] = (value, 1)
            self.freq_to_keys[1][key] = None
            self.min_freq = 1

    def get(self, key):
        """
        Получить значение по ключу

        Args:
            key: Ключ для поиска

        Returns:
            Значение или None если не найдено
        """
        if key not in self.key_to_val_freq:
            self.misses += 1
            return None

        # Обновляем частоту
        self._update_freq(key)
        self.hits += 1
        return self.key_to_val_freq[key][0]

    def set(self, key, value):
        """
        Установить значение по ключу

        Args:
            key: Ключ
            value: Значение
        """
        if self.capacity == 0:
            return

        if key in self.key_to_val_freq:
            # Обновляем существующий ключ
            self._update_freq(key, value)
        else:
            # Новый ключ - проверяем размер
            if len(self.key_to_val_freq) >= self.capacity:
                # Удаляем элемент с минимальной частотой
                # (первый в OrderedDict для этой частоты - LRU среди равных)
                evict_key = next(iter(self.freq_to_keys[self.min_freq]))
                del self.freq_to_keys[self.min_freq][evict_key]
                if len(self.freq_to_keys[self.min_freq]) == 0:
                    del self.freq_to_keys[self.min_freq]
                del self.key_to_val_freq[evict_key]
                self.evictions += 1

            # Добавляем новый ключ
            self._update_freq(key, value)

    def delete(self, key):
        """Удалить элемент из кэша"""
        if key in self.key_to_val_freq:
            _, freq = self.key_to_val_freq[key]
            del self.key_to_val_freq[key]
            del self.freq_to_keys[freq][key]
            if len(self.freq_to_keys[freq]) == 0:
                del self.freq_to_keys[freq]
                if self.min_freq == freq and len(self.key_to_val_freq) > 0:
                    self.min_freq = min(self.freq_to_keys.keys())
            return True
        return False

    def clear(self):
        """Очистить кэш"""
        self.key_to_val_freq.clear()
        self.freq_to_keys.clear()
        self.min_freq = 0
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def size(self):
        """Текущий размер кэша"""
        return len(self.key_to_val_freq)

    def get_frequency_distribution(self):
        """Получить распределение частот"""
        dist = {}
        for freq, keys in self.freq_to_keys.items():
            dist[freq] = len(keys)
        return dist

    def get_stats(self):
        """Получить статистику"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0

        return {
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions,
            'hit_rate': hit_rate,
            'current_size': len(self.key_to_val_freq),
            'capacity': self.capacity,
            'min_frequency': self.min_freq,
            'frequency_distribution': self.get_frequency_distribution()
        }


class LFUCacheWithDecay:
    """
    LFU кэш с затуханием частот

    Периодически уменьшает частоты для адаптации к изменениям паттернов
    """

    def __init__(self, capacity, decay_factor=0.5, decay_interval=100):
        """
        Инициализация LFU кэша с затуханием

        Args:
            capacity: Максимальный размер кэша
            decay_factor: Коэффициент затухания (0.5 = половина частоты)
            decay_interval: Интервал операций между затуханиями
        """
        self.base_cache = LFUCache(capacity)
        self.decay_factor = decay_factor
        self.decay_interval = decay_interval
        self.operations = 0

    def _maybe_decay(self):
        """Применить затухание если нужно"""
        self.operations += 1
        if self.operations % self.decay_interval == 0:
            # Применяем затухание ко всем частотам
            new_key_to_val_freq = {}
            new_freq_to_keys = defaultdict(OrderedDict)

            for key, (value, freq) in self.base_cache.key_to_val_freq.items():
                new_freq = max(1, int(freq * self.decay_factor))
                new_key_to_val_freq[key] = (value, new_freq)
                new_freq_to_keys[new_freq][key] = None

            self.base_cache.key_to_val_freq = new_key_to_val_freq
            self.base_cache.freq_to_keys = new_freq_to_keys
            if new_freq_to_keys:
                self.base_cache.min_freq = min(new_freq_to_keys.keys())

    def get(self, key):
        """Получить значение с учётом затухания"""
        self._maybe_decay()
        return self.base_cache.get(key)

    def set(self, key, value):
        """Установить значение с учётом затухания"""
        self._maybe_decay()
        self.base_cache.set(key, value)

    def get_stats(self):
        """Получить статистику"""
        stats = self.base_cache.get_stats()
        stats['decay_factor'] = self.decay_factor
        stats['decay_interval'] = self.decay_interval
        stats['operations'] = self.operations
        return stats


def demo():
    """Демонстрация работы LFU кэша"""
    print("=== LFU Cache Demo ===\n")

    cache = LFUCache(3)

    print("1. Начальное заполнение (capacity=3):")
    items = [("a", 1), ("b", 2), ("c", 3)]
    for key, val in items:
        cache.set(key, val)
        print(f"   set('{key}', {val})")

    print("\n2. Создаём разные частоты использования:")
    # 'a' используем 3 раза
    for _ in range(3):
        cache.get("a")
        print("   get('a')")

    # 'b' используем 2 раза
    for _ in range(2):
        cache.get("b")
        print("   get('b')")

    # 'c' используем 1 раз
    cache.get("c")
    print("   get('c')")

    print(f"\n   Распределение частот: {cache.get_frequency_distribution()}")

    print("\n3. Добавляем новый элемент:")
    cache.set("d", 4)
    print("   set('d', 4)")
    print("   Должен быть вытеснен 'c' (наименьшая частота)")

    print("\n4. Проверка содержимого:")
    for key in ["a", "b", "c", "d"]:
        val = cache.get(key)
        if val:
            freq = cache.key_to_val_freq[key][1]
            print(f"   '{key}': есть (freq={freq})")
        else:
            print(f"   '{key}': вытеснен")

    print("\n5. Статистика:")
    stats = cache.get_stats()
    for key, value in stats.items():
        if key == 'hit_rate':
            print(f"   {key}: {value:.2%}")
        elif key != 'frequency_distribution':
            print(f"   {key}: {value}")
    print(f"   frequency_distribution: {stats['frequency_distribution']}")


def demo_decay():
    """Демонстрация LFU с затуханием"""
    print("\n=== LFU with Decay Demo ===\n")

    cache = LFUCacheWithDecay(5, decay_factor=0.5, decay_interval=10)

    print("1. Создаём начальный 'горячий' набор:")
    hot_keys = ["hot_1", "hot_2", "hot_3"]
    for key in hot_keys:
        cache.set(key, key)
        # Много обращений
        for _ in range(10):
            cache.get(key)

    stats = cache.get_stats()
    print(f"   Частоты после 'разогрева': {stats['frequency_distribution']}")

    print("\n2. Добавляем новые элементы (имитация смены паттерна):")
    # Выполняем операции до затухания
    for i in range(15):
        key = f"new_{i}"
        cache.set(key, key)
        cache.get(key)

    stats = cache.get_stats()
    print(f"   Частоты после затухания: {stats['frequency_distribution']}")
    print(f"   Операций выполнено: {stats['operations']}")

    print("\n3. Проверка адаптации:")
    for key in hot_keys[:2]:
        val = cache.get(key)
        print(f"   Старый 'горячий' '{key}': {'сохранён' if val else 'вытеснен'}")


def benchmark():
    """Сравнение LFU с LRU"""
    print("\n=== LFU vs LRU Benchmark ===\n")

    from lru_doubly_linked_list import LRUCache
    import random

    scenarios = [
        ("Zipf Distribution (realistic)", "zipf"),
        ("Uniform Random", "uniform"),
        ("Working Set Change", "change")
    ]

    capacity = 100
    requests = 10000

    for scenario_name, scenario_type in scenarios:
        print(f"{scenario_name}:")
        print("-" * 40)

        lfu = LFUCache(capacity)
        lru = LRUCache(capacity)

        if scenario_type == "zipf":
            # Zipf распределение (несколько ключей очень популярны)
            keys = list(range(500))
            # Веса по закону Zipf
            weights = [1.0 / (i + 1) for i in range(len(keys))]
            total_weight = sum(weights)
            weights = [w / total_weight for w in weights]

            for _ in range(requests):
                # Выбираем ключ с учётом весов
                r = random.random()
                cumsum = 0
                for i, w in enumerate(weights):
                    cumsum += w
                    if r < cumsum:
                        key = keys[i]
                        break

                # Пытаемся получить
                if not lfu.get(key):
                    lfu.set(key, key)
                if not lru.get(key):
                    lru.set(key, key)

        elif scenario_type == "uniform":
            # Равномерное распределение
            keys = list(range(300))

            for _ in range(requests):
                key = random.choice(keys)

                if not lfu.get(key):
                    lfu.set(key, key)
                if not lru.get(key):
                    lru.set(key, key)

        else:  # change
            # Меняющийся рабочий набор
            # Первая половина - один набор
            keys1 = list(range(150))
            for _ in range(requests // 2):
                key = random.choice(keys1)
                if not lfu.get(key):
                    lfu.set(key, key)
                if not lru.get(key):
                    lru.set(key, key)

            # Вторая половина - другой набор
            keys2 = list(range(100, 250))
            for _ in range(requests // 2):
                key = random.choice(keys2)
                if not lfu.get(key):
                    lfu.set(key, key)
                if not lru.get(key):
                    lru.set(key, key)

        lfu_stats = lfu.get_stats()
        lru_stats = lru.get_stats()

        print(f"  LFU:")
        print(f"    Hit rate: {lfu_stats['hit_rate']:.2%}")
        print(f"    Evictions: {lfu_stats['evictions']}")

        print(f"  LRU:")
        print(f"    Hit rate: {lru_stats['hit_rate']:.2%}")
        print(f"    Evictions: {lru_stats['evictions']}")

        winner = "LFU" if lfu_stats['hit_rate'] > lru_stats['hit_rate'] else "LRU"
        improvement = abs(lfu_stats['hit_rate'] - lru_stats['hit_rate'])
        print(f"  Winner: {winner} (+{improvement:.1%})\n")


def test_correctness():
    """Тесты корректности LFU кэша"""
    print("\n=== LFU Correctness Tests ===\n")

    # Тест 1: Базовая функциональность
    cache = LFUCache(2)
    cache.set("a", 1)
    cache.set("b", 2)

    # Увеличиваем частоту 'a'
    cache.get("a")
    cache.get("a")

    # Добавляем 'c' - должен вытеснить 'b' (меньшая частота)
    cache.set("c", 3)

    assert cache.get("a") == 1, "'a' should exist (high frequency)"
    assert cache.get("b") is None, "'b' should be evicted (lowest frequency)"
    assert cache.get("c") == 3, "'c' should exist"
    print("✓ Test 1: Basic LFU eviction by frequency")

    # Тест 2: LRU среди равных частот
    cache = LFUCache(2)
    cache.set("a", 1)
    cache.set("b", 2)

    # Обе частоты = 1, добавляем 'c'
    cache.set("c", 3)

    # Должен быть вытеснен 'a' (старейший среди равных)
    assert cache.get("a") is None, "'a' should be evicted (LRU among equal freq)"
    assert cache.get("b") == 2, "'b' should exist"
    assert cache.get("c") == 3, "'c' should exist"
    print("✓ Test 2: LRU tie-breaking among equal frequencies")

    # Тест 3: Обновление существующего ключа
    cache = LFUCache(2)
    cache.set("a", 1)
    cache.get("a")  # freq = 2
    cache.set("b", 2)  # freq = 1

    cache.set("a", 10)  # Обновление, freq теперь 3
    cache.set("c", 3)   # Должен вытеснить 'b'

    assert cache.get("a") == 10, "'a' should be updated"
    assert cache.get("b") is None, "'b' should be evicted"
    assert cache.get("c") == 3, "'c' should exist"
    print("✓ Test 3: Update increases frequency")

    # Тест 4: Затухание частот
    cache = LFUCacheWithDecay(3, decay_factor=0.5, decay_interval=5)

    # Создаём высокие частоты
    cache.set("a", 1)
    for _ in range(10):
        cache.get("a")  # Высокая частота

    cache.set("b", 2)
    cache.set("c", 3)

    # Выполняем операции до затухания
    for i in range(6):
        cache.set(f"trigger_{i}", i)

    # После затухания частоты должны уменьшиться
    stats = cache.get_stats()
    max_freq = max(stats['frequency_distribution'].keys())
    assert max_freq <= 6, f"Frequencies should decay, max={max_freq}"
    print("✓ Test 4: Frequency decay works")

    print("\nAll tests passed!")


if __name__ == "__main__":
    demo()
    demo_decay()
    benchmark()
    test_correctness()
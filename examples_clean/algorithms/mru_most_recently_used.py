#!/usr/bin/env python3
"""
MRU (Most Recently Used) Cache - полная реализация

MRU удаляет НАИБОЛЕЕ недавно использованные элементы,
когда кэш заполнен. Эффективен для сканирующих паттернов доступа.
"""

from collections import OrderedDict
import time
import random


class MRUCache:
    """MRU кэш на основе OrderedDict"""

    def __init__(self, capacity):
        """
        Инициализация MRU кэша

        Args:
            capacity: Максимальный размер кэша
        """
        if capacity <= 0:
            raise ValueError("Capacity must be positive")

        self.capacity = capacity
        self.cache = OrderedDict()

        # Статистика
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def get(self, key):
        """
        Получить значение по ключу

        Args:
            key: Ключ для поиска

        Returns:
            Значение или None если не найдено
        """
        if key not in self.cache:
            self.misses += 1
            return None

        # Также перемещаем в конец (для отслеживания использования)
        self.cache.move_to_end(key)
        self.hits += 1
        return self.cache[key]

    def set(self, key, value):
        """
        Установить значение по ключу

        Args:
            key: Ключ
            value: Значение
        """
        if key in self.cache:
            # Обновляем существующий ключ
            self.cache.move_to_end(key)
        else:
            # Новый ключ
            if len(self.cache) >= self.capacity:
                # Удаляем ПОСЛЕДНИЙ элемент (самый свежий!)
                # Это главное отличие от LRU
                evicted = self.cache.popitem(last=True)
                self.evictions += 1

        self.cache[key] = value

    def delete(self, key):
        """Удалить элемент из кэша"""
        if key in self.cache:
            del self.cache[key]
            return True
        return False

    def clear(self):
        """Очистить кэш"""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def size(self):
        """Текущий размер кэша"""
        return len(self.cache)

    def peek(self):
        """Посмотреть все ключи в порядке от старого к новому"""
        return list(self.cache.keys())

    def get_stats(self):
        """Получить статистику"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0

        return {
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions,
            'hit_rate': hit_rate,
            'current_size': len(self.cache),
            'capacity': self.capacity
        }


class MRUCacheWithProbability:
    """
    MRU кэш с вероятностным удалением

    Вместо всегда удаления самого недавнего, удаляет
    с вероятностью, зависящей от давности использования
    """

    def __init__(self, capacity, mru_probability=0.8):
        """
        Инициализация MRU кэша с вероятностным удалением

        Args:
            capacity: Максимальный размер кэша
            mru_probability: Вероятность удаления самого недавнего элемента
        """
        if capacity <= 0:
            raise ValueError("Capacity must be positive")

        self.capacity = capacity
        self.cache = OrderedDict()
        self.mru_probability = mru_probability

        # Статистика
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.mru_evictions = 0

    def get(self, key):
        """
        Получить значение по ключу

        Args:
            key: Ключ для поиска

        Returns:
            Значение или None если не найдено
        """
        if key not in self.cache:
            self.misses += 1
            return None

        self.cache.move_to_end(key)
        self.hits += 1
        return self.cache[key]

    def set(self, key, value):
        """
        Установить значение по ключу

        Args:
            key: Ключ
            value: Значение
        """
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.capacity:
                # Вероятностное удаление
                if random.random() < self.mru_probability:
                    # Удаляем самый недавний (MRU)
                    evicted = self.cache.popitem(last=True)
                    self.mru_evictions += 1
                else:
                    # Удаляем случайный элемент
                    keys = list(self.cache.keys())
                    random_key = random.choice(keys[:-1])  # Исключаем последний
                    del self.cache[random_key]

                self.evictions += 1

        self.cache[key] = value

    def get_stats(self):
        """Получить расширенную статистику"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0

        return {
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions,
            'mru_evictions': self.mru_evictions,
            'random_evictions': self.evictions - self.mru_evictions,
            'hit_rate': hit_rate,
            'current_size': len(self.cache),
            'capacity': self.capacity,
            'mru_probability': self.mru_probability
        }


def demo():
    """Демонстрация работы MRU кэша"""
    print("=== MRU Cache Demo ===\n")

    # Создаём обычный MRU кэш
    cache = MRUCache(3)

    print("1. Последовательное заполнение (capacity=3):")
    for i in range(4):
        cache.set(f"key_{i}", f"value_{i}")
        print(f"   set('key_{i}', 'value_{i}')")
        print(f"   Текущие ключи: {cache.peek()}")

    print(f"\n   Вытеснений: {cache.get_stats()['evictions']}")
    print("   Заметьте: key_2 был удалён (он был самым недавним при добавлении key_3)")
    print()

    # Паттерн сканирования
    print("2. Паттерн сканирования (чтение большого массива один раз):")
    cache = MRUCache(5)

    # Загружаем "рабочий набор"
    working_set = ["work_1", "work_2", "work_3"]
    for key in working_set:
        cache.set(key, f"value_{key}")

    print(f"   Рабочий набор: {working_set}")

    # Сканирование большого массива
    scan_data = [f"scan_{i}" for i in range(10)]
    print(f"   Сканирование: {scan_data}")

    for key in scan_data:
        cache.set(key, f"value_{key}")

    # Проверяем что осталось
    print("\n   После сканирования:")
    for key in working_set:
        val = cache.get(key)
        print(f"   '{key}': {'сохранён' if val else 'вытеснен'}")

    stats = cache.get_stats()
    print(f"\n   Статистика:")
    print(f"   Hit rate: {stats['hit_rate']:.2%}")
    print(f"   Вытеснений: {stats['evictions']}")
    print()

    # Вероятностный MRU
    print("3. Вероятностный MRU кэш:")
    prob_cache = MRUCacheWithProbability(3, mru_probability=0.7)

    for i in range(10):
        prob_cache.set(f"key_{i}", f"value_{i}")

    stats = prob_cache.get_stats()
    print(f"   MRU вытеснений: {stats['mru_evictions']}")
    print(f"   Случайных вытеснений: {stats['random_evictions']}")
    print(f"   Соотношение: {stats['mru_evictions']}/{stats['evictions']}")


def compare_with_lru():
    """Сравнение MRU и LRU на разных паттернах"""
    print("\n=== MRU vs LRU Comparison ===\n")

    # Импортируем LRU для сравнения
    from lru_doubly_linked_list import LRUCache

    scenarios = [
        ("Sequential Scan", "sequential"),
        ("Random Access", "random"),
        ("Loop with Working Set", "loop"),
        ("80/20 Pattern", "pareto")
    ]

    capacity = 50
    data_size = 200
    requests = 1000

    for scenario_name, scenario_type in scenarios:
        print(f"{scenario_name}:")
        print("-" * 40)

        mru = MRUCache(capacity)
        lru = LRUCache(capacity)

        if scenario_type == "sequential":
            # Последовательное сканирование
            # Сначала загружаем рабочий набор
            for i in range(20):
                key = f"work_{i}"
                mru.set(key, i)
                lru.set(key, i)

            # Затем сканирование
            for i in range(data_size):
                key = f"scan_{i}"
                mru.set(key, i)
                lru.set(key, i)

            # Проверяем рабочий набор
            for i in range(20):
                key = f"work_{i}"
                mru.get(key)
                lru.get(key)

        elif scenario_type == "random":
            # Случайный доступ
            keys = [f"key_{i}" for i in range(data_size)]

            for _ in range(requests):
                key = random.choice(keys)
                value = random.randint(0, 1000)

                mru.set(key, value)
                lru.set(key, value)

                if random.random() < 0.5:
                    mru.get(key)
                    lru.get(key)

        elif scenario_type == "loop":
            # Цикличный доступ с рабочим набором
            working_keys = [f"work_{i}" for i in range(30)]
            loop_keys = [f"loop_{i}" for i in range(60)]

            # Загружаем рабочий набор
            for key in working_keys:
                mru.set(key, key)
                lru.set(key, key)

            # Цикличный доступ
            for _ in range(5):
                for key in loop_keys:
                    mru.set(key, key)
                    lru.set(key, key)

                # Проверяем рабочий набор
                for key in working_keys[:10]:
                    mru.get(key)
                    lru.get(key)

        else:  # pareto (80/20)
            # 20% ключей получают 80% запросов
            hot_keys = [f"hot_{i}" for i in range(int(data_size * 0.2))]
            cold_keys = [f"cold_{i}" for i in range(int(data_size * 0.8))]

            # Начальная загрузка
            for key in hot_keys + cold_keys:
                mru.set(key, key)
                lru.set(key, key)

            for _ in range(requests):
                if random.random() < 0.8:
                    key = random.choice(hot_keys)
                else:
                    key = random.choice(cold_keys)

                val_mru = mru.get(key)
                val_lru = lru.get(key)

                if not val_mru:
                    mru.set(key, key)
                if not val_lru:
                    lru.set(key, key)

        # Результаты
        mru_stats = mru.get_stats()
        lru_stats = lru.get_stats()

        print(f"  MRU:")
        print(f"    Hit rate: {mru_stats['hit_rate']:.2%}")
        print(f"    Evictions: {mru_stats['evictions']}")

        print(f"  LRU:")
        print(f"    Hit rate: {lru_stats['hit_rate']:.2%}")
        print(f"    Evictions: {lru_stats['evictions']}")

        winner = "MRU" if mru_stats['hit_rate'] > lru_stats['hit_rate'] else "LRU"
        print(f"  Winner: {winner}\n")


def test_correctness():
    """Тесты корректности MRU кэша"""
    print("\n=== MRU Correctness Tests ===\n")

    # Тест 1: Базовая функциональность
    cache = MRUCache(2)
    cache.set("a", 1)
    cache.set("b", 2)
    assert cache.get("a") == 1, "Failed to get 'a'"
    assert cache.get("b") == 2, "Failed to get 'b'"

    cache.set("c", 3)  # Должен вытеснить 'b' (самый недавний)
    assert cache.get("a") == 1, "'a' should still exist"
    assert cache.get("b") is None, "'b' should be evicted (was MRU)"
    assert cache.get("c") == 3, "'c' should exist"
    print("✓ Test 1: Basic MRU eviction")

    # Тест 2: Обновление существующего ключа
    cache = MRUCache(2)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.set("a", 10)  # Обновление делает 'a' самым недавним
    cache.set("c", 3)   # Должен вытеснить 'a' (теперь он MRU)

    assert cache.get("a") is None, "'a' should be evicted (became MRU after update)"
    assert cache.get("b") == 2, "'b' should still exist"
    assert cache.get("c") == 3, "'c' should exist"
    print("✓ Test 2: Update makes key MRU")

    # Тест 3: Паттерн сканирования
    cache = MRUCache(5)

    # Загружаем стабильный рабочий набор
    for i in range(3):
        cache.set(f"stable_{i}", i)

    # Сканирование не должно вытеснить весь рабочий набор
    for i in range(10):
        cache.set(f"scan_{i}", i)

    # Проверяем что хотя бы часть рабочего набора сохранилась
    preserved = sum(1 for i in range(3) if cache.get(f"stable_{i}") is not None)
    assert preserved >= 2, f"MRU should preserve most of working set, got {preserved}/3"
    print(f"✓ Test 3: Scan resistance (preserved {preserved}/3 working set items)")

    # Тест 4: Вероятностный MRU
    prob_cache = MRUCacheWithProbability(10, mru_probability=0.7)

    for i in range(100):
        prob_cache.set(f"key_{i}", i)

    stats = prob_cache.get_stats()
    mru_ratio = stats['mru_evictions'] / stats['evictions'] if stats['evictions'] > 0 else 0

    # Проверяем что соотношение близко к заданной вероятности
    assert 0.5 < mru_ratio < 0.9, f"MRU eviction ratio {mru_ratio} not close to 0.7"
    print(f"✓ Test 4: Probabilistic MRU (ratio: {mru_ratio:.2f})")

    print("\nAll tests passed!")


if __name__ == "__main__":
    demo()
    compare_with_lru()
    test_correctness()
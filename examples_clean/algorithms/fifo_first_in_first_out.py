#!/usr/bin/env python3
"""
FIFO (First In First Out) Cache - полная реализация

FIFO удаляет элементы в том порядке, в котором они были добавлены,
независимо от частоты использования. Простейшая стратегия вытеснения.
"""

from collections import OrderedDict, deque
import time
import random


class FIFOCache:
    """FIFO кэш на основе OrderedDict"""

    def __init__(self, capacity):
        """
        Инициализация FIFO кэша

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

        # В FIFO НЕ перемещаем элементы при доступе
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
            # Обновляем существующий ключ БЕЗ изменения позиции
            self.cache[key] = value
        else:
            # Новый ключ - проверяем размер
            if len(self.cache) >= self.capacity:
                # Удаляем первый элемент (самый старый по времени добавления)
                evicted = self.cache.popitem(last=False)
                self.evictions += 1

            # Добавляем в конец
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

    def peek_order(self):
        """Посмотреть порядок элементов (от старого к новому)"""
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


class FIFOCacheDeque:
    """Альтернативная реализация FIFO через deque и dict"""

    def __init__(self, capacity):
        """
        Инициализация FIFO кэша с deque

        Args:
            capacity: Максимальный размер кэша
        """
        if capacity <= 0:
            raise ValueError("Capacity must be positive")

        self.capacity = capacity
        self.cache = {}  # key -> value
        self.order = deque()  # Порядок добавления

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
            self.cache[key] = value
        else:
            # Новый ключ
            if len(self.cache) >= self.capacity:
                # Удаляем самый старый
                old_key = self.order.popleft()
                del self.cache[old_key]
                self.evictions += 1

            # Добавляем новый
            self.cache[key] = value
            self.order.append(key)

    def delete(self, key):
        """Удалить элемент из кэша"""
        if key in self.cache:
            del self.cache[key]
            self.order.remove(key)  # O(n) операция
            return True
        return False

    def clear(self):
        """Очистить кэш"""
        self.cache.clear()
        self.order.clear()
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def size(self):
        """Текущий размер кэша"""
        return len(self.cache)

    def peek_order(self):
        """Посмотреть порядок элементов"""
        return list(self.order)

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


class FIFOWithSecondChance:
    """
    FIFO с второй возможностью (Clock algorithm)

    Дает элементам второй шанс если к ним недавно обращались
    """

    def __init__(self, capacity):
        """
        Инициализация FIFO с второй возможностью

        Args:
            capacity: Максимальный размер кэша
        """
        if capacity <= 0:
            raise ValueError("Capacity must be positive")

        self.capacity = capacity
        self.cache = {}  # key -> (value, reference_bit)
        self.order = deque()  # Циклический порядок
        self.clock_hand = 0  # Указатель на текущий элемент

        # Статистика
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        self.second_chances = 0

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

        # Устанавливаем бит обращения
        value, _ = self.cache[key]
        self.cache[key] = (value, True)
        self.hits += 1
        return value

    def set(self, key, value):
        """
        Установить значение по ключу

        Args:
            key: Ключ
            value: Значение
        """
        if key in self.cache:
            # Обновляем существующий ключ
            self.cache[key] = (value, True)
        else:
            # Новый ключ
            if len(self.cache) >= self.capacity:
                # Ищем жертву с помощью алгоритма часов
                self._evict_with_clock()

            # Добавляем новый элемент
            self.cache[key] = (value, False)
            self.order.append(key)

    def _evict_with_clock(self):
        """Найти и удалить жертву с помощью алгоритма часов"""
        while True:
            if self.clock_hand >= len(self.order):
                self.clock_hand = 0

            key = self.order[self.clock_hand]
            value, ref_bit = self.cache[key]

            if not ref_bit:
                # Нашли жертву
                del self.cache[key]
                del self.order[self.clock_hand]
                self.evictions += 1
                if self.clock_hand >= len(self.order) and self.order:
                    self.clock_hand = 0
                return
            else:
                # Даем второй шанс
                self.cache[key] = (value, False)
                self.second_chances += 1
                self.clock_hand += 1

    def get_stats(self):
        """Получить расширенную статистику"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0

        return {
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions,
            'second_chances': self.second_chances,
            'hit_rate': hit_rate,
            'current_size': len(self.cache),
            'capacity': self.capacity
        }


def demo():
    """Демонстрация работы FIFO кэша"""
    print("=== FIFO Cache Demo ===\n")

    cache = FIFOCache(4)

    print("1. Последовательное заполнение (capacity=4):")
    for i in range(6):
        cache.set(f"key_{i}", f"value_{i}")
        print(f"   set('key_{i}', 'value_{i}')")
        print(f"   Порядок: {cache.peek_order()}")

    print(f"\n   Вытеснений: {cache.get_stats()['evictions']}")
    print("   key_0 и key_1 были удалены первыми (FIFO порядок)")

    print("\n2. Обращения НЕ меняют порядок в FIFO:")
    # Обращаемся к элементам
    keys_to_access = ["key_2", "key_3", "key_4", "key_5"]
    for key in keys_to_access:
        val = cache.get(key)
        if val:
            print(f"   get('{key}') -> HIT: {val}")
        else:
            print(f"   get('{key}') -> MISS")

    print(f"   Порядок остался: {cache.peek_order()}")

    print("\n3. Добавление нового элемента:")
    cache.set("key_new", "value_new")
    print("   set('key_new', 'value_new')")
    print(f"   Новый порядок: {cache.peek_order()}")
    print("   key_2 удален (самый старый)")

    print("\n4. Статистика:")
    stats = cache.get_stats()
    for key, value in stats.items():
        if key == 'hit_rate':
            print(f"   {key}: {value:.2%}")
        else:
            print(f"   {key}: {value}")


def demo_second_chance():
    """Демонстрация FIFO с второй возможностью"""
    print("\n=== FIFO with Second Chance Demo ===\n")

    cache = FIFOWithSecondChance(3)

    print("1. Заполнение кэша:")
    for i in range(3):
        cache.set(f"key_{i}", f"value_{i}")
        print(f"   set('key_{i}', 'value_{i}')")

    print("\n2. Обращение к key_0 (устанавливает reference bit):")
    cache.get("key_0")
    print("   get('key_0')")

    print("\n3. Добавление нового элемента:")
    cache.set("key_3", "value_3")
    print("   set('key_3', 'value_3')")
    print("   key_0 получил второй шанс, key_1 был удален")

    print("\n4. Проверка содержимого:")
    for i in range(4):
        key = f"key_{i}"
        val = cache.get(key)
        print(f"   '{key}': {'есть' if val else 'удален'}")

    print("\n5. Статистика:")
    stats = cache.get_stats()
    for key, value in stats.items():
        if key == 'hit_rate':
            print(f"   {key}: {value:.2%}")
        else:
            print(f"   {key}: {value}")


def benchmark():
    """Сравнение FIFO с другими алгоритмами"""
    print("\n=== FIFO vs Other Algorithms ===\n")

    from lru_doubly_linked_list import LRUCache
    from lfu_least_frequently_used import LFUCache

    scenarios = [
        ("Sequential Access", "sequential"),
        ("Working Set", "working_set"),
        ("Random Access", "random")
    ]

    capacity = 50
    requests = 2000

    for scenario_name, scenario_type in scenarios:
        print(f"{scenario_name}:")
        print("-" * 40)

        fifo = FIFOCache(capacity)
        lru = LRUCache(capacity)
        lfu = LFUCache(capacity)

        if scenario_type == "sequential":
            # Последовательный доступ к большому диапазону
            for i in range(requests):
                key = f"key_{i}"
                for cache in [fifo, lru, lfu]:
                    cache.set(key, i)

        elif scenario_type == "working_set":
            # Рабочий набор + редкие внешние обращения
            working_set = [f"work_{i}" for i in range(30)]
            external_set = [f"ext_{i}" for i in range(100)]

            for i in range(requests):
                if i % 10 == 0:
                    # Редкое внешнее обращение
                    key = random.choice(external_set)
                else:
                    # Обычный рабочий набор
                    key = random.choice(working_set)

                for cache in [fifo, lru, lfu]:
                    val = cache.get(key)
                    if not val:
                        cache.set(key, key)

        else:  # random
            # Случайный доступ
            keys = [f"key_{i}" for i in range(200)]

            for _ in range(requests):
                key = random.choice(keys)
                for cache in [fifo, lru, lfu]:
                    val = cache.get(key)
                    if not val:
                        cache.set(key, key)

        # Результаты
        fifo_stats = fifo.get_stats()
        lru_stats = lru.get_stats()
        lfu_stats = lfu.get_stats()

        results = [
            ("FIFO", fifo_stats),
            ("LRU", lru_stats),
            ("LFU", lfu_stats)
        ]

        results.sort(key=lambda x: x[1]['hit_rate'], reverse=True)

        for i, (name, stats) in enumerate(results):
            prefix = f"  {i+1}. {name}:"
            print(f"{prefix}")
            print(f"    Hit rate: {stats['hit_rate']:.2%}")
            print(f"    Evictions: {stats['evictions']}")

        print()


def performance_test():
    """Тест производительности разных реализаций FIFO"""
    print("\n=== FIFO Performance Test ===\n")

    implementations = [
        ("OrderedDict", FIFOCache),
        ("Deque", FIFOCacheDeque),
        ("Second Chance", FIFOWithSecondChance)
    ]

    sizes = [100, 1000, 5000]
    operations = 10000

    for size in sizes:
        print(f"Cache size: {size}")
        print("-" * 30)

        for name, cache_class in implementations:
            cache = cache_class(size)

            start = time.time()
            for i in range(operations):
                cache.set(f"key_{i % (size * 2)}", f"value_{i}")
                cache.get(f"key_{i % (size * 2)}")

            elapsed = time.time() - start
            stats = cache.get_stats()

            print(f"  {name}:")
            print(f"    Time: {elapsed:.4f}s")
            print(f"    Hit rate: {stats['hit_rate']:.2%}")

        print()


def test_correctness():
    """Тесты корректности FIFO кэшей"""
    print("\n=== FIFO Correctness Tests ===\n")

    def test_implementation(cache_class, name):
        print(f"Testing {name}:")

        # Тест 1: Базовая функциональность FIFO
        cache = cache_class(2)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)  # Должен вытеснить 'a'

        assert cache.get("a") is None, "'a' should be evicted (first in, first out)"
        assert cache.get("b") == 2, "'b' should exist"
        assert cache.get("c") == 3, "'c' should exist"
        print(f"  ✓ Basic FIFO eviction")

        # Тест 2: Обращения не влияют на порядок
        cache = cache_class(2)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.get("a")  # В FIFO это не должно влиять на порядок
        cache.set("c", 3)  # Все равно должен вытеснить 'a'

        assert cache.get("a") is None, "'a' should be evicted despite recent access"
        assert cache.get("b") == 2, "'b' should exist"
        assert cache.get("c") == 3, "'c' should exist"
        print(f"  ✓ Access doesn't change eviction order")

        # Тест 3: Обновление существующего ключа
        cache = cache_class(2)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("a", 10)  # Обновление
        cache.set("c", 3)   # Должен вытеснить 'b'

        assert cache.get("a") == 10, "'a' should be updated"
        assert cache.get("b") is None, "'b' should be evicted"
        assert cache.get("c") == 3, "'c' should exist"
        print(f"  ✓ Update existing key")

        print(f"  All tests passed for {name}!\n")

    test_implementation(FIFOCache, "OrderedDict FIFO")
    test_implementation(FIFOCacheDeque, "Deque FIFO")

    # Специальный тест для Second Chance
    print("Testing Second Chance FIFO:")
    cache = FIFOWithSecondChance(2)
    cache.set("a", 1)
    cache.set("b", 2)
    cache.get("a")  # Устанавливает reference bit
    cache.set("c", 3)  # 'a' получает второй шанс, 'b' удаляется

    assert cache.get("a") == 1, "'a' should get second chance"
    assert cache.get("b") is None, "'b' should be evicted"
    assert cache.get("c") == 3, "'c' should exist"
    print("  ✓ Second chance mechanism")
    print("  All tests passed for Second Chance FIFO!\n")


if __name__ == "__main__":
    demo()
    demo_second_chance()
    benchmark()
    performance_test()
    test_correctness()
#!/usr/bin/env python3
"""
LRU (Least Recently Used) Cache - полная реализация

LRU удаляет наименее недавно использованные элементы,
когда кэш заполнен. Реализация через OrderedDict и
альтернативная через двусвязный список.
"""

from collections import OrderedDict
import time


class LRUCache:
    """LRU кэш на основе OrderedDict"""

    def __init__(self, capacity):
        """
        Инициализация LRU кэша

        Args:
            capacity: Максимальный размер кэша
        """
        if capacity <= 0:
            raise ValueError("Capacity must be positive")

        self.capacity = capacity
        self.cache = OrderedDict()  # Сохраняет порядок вставки

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

        # Перемещаем в конец (самый свежий)
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
                # Удаляем первый элемент (самый старый)
                evicted = self.cache.popitem(last=False)
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


class Node:
    """Узел для двусвязного списка"""

    def __init__(self, key=None, value=None):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None


class LRUCacheDoublyLinked:
    """LRU кэш через двусвязный список (классическая реализация)"""

    def __init__(self, capacity):
        """
        Инициализация LRU кэша с двусвязным списком

        Args:
            capacity: Максимальный размер кэша
        """
        if capacity <= 0:
            raise ValueError("Capacity must be positive")

        self.capacity = capacity
        self.cache = {}  # key -> node mapping

        # Создаём фиктивные голову и хвост
        self.head = Node()
        self.tail = Node()
        self.head.next = self.tail
        self.tail.prev = self.head

        # Статистика
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def _add_node(self, node):
        """Добавить узел в конец (перед tail)"""
        prev_node = self.tail.prev
        prev_node.next = node
        node.prev = prev_node
        node.next = self.tail
        self.tail.prev = node

    def _remove_node(self, node):
        """Удалить узел из списка"""
        prev_node = node.prev
        next_node = node.next
        prev_node.next = next_node
        next_node.prev = prev_node

    def _move_to_end(self, node):
        """Переместить узел в конец"""
        self._remove_node(node)
        self._add_node(node)

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

        node = self.cache[key]
        self._move_to_end(node)
        self.hits += 1
        return node.value

    def set(self, key, value):
        """
        Установить значение по ключу

        Args:
            key: Ключ
            value: Значение
        """
        if key in self.cache:
            # Обновляем существующий узел
            node = self.cache[key]
            node.value = value
            self._move_to_end(node)
        else:
            # Новый узел
            if len(self.cache) >= self.capacity:
                # Удаляем самый старый (после head)
                lru_node = self.head.next
                self._remove_node(lru_node)
                del self.cache[lru_node.key]
                self.evictions += 1

            # Добавляем новый узел
            new_node = Node(key, value)
            self.cache[key] = new_node
            self._add_node(new_node)

    def delete(self, key):
        """Удалить элемент из кэша"""
        if key in self.cache:
            node = self.cache[key]
            self._remove_node(node)
            del self.cache[key]
            return True
        return False

    def clear(self):
        """Очистить кэш"""
        self.cache.clear()
        self.head.next = self.tail
        self.tail.prev = self.head
        self.hits = 0
        self.misses = 0
        self.evictions = 0

    def size(self):
        """Текущий размер кэша"""
        return len(self.cache)

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


def demo():
    """Демонстрация работы LRU кэша"""
    print("=== LRU Cache Demo ===\n")

    # Тестируем обе реализации
    implementations = [
        ("OrderedDict", LRUCache(3)),
        ("Doubly Linked List", LRUCacheDoublyLinked(3))
    ]

    for name, cache in implementations:
        print(f"Implementation: {name}")
        print("-" * 40)

        # Заполняем кэш
        print("1. Заполнение кэша (capacity=3):")
        for i in range(4):
            cache.set(f"key_{i}", f"value_{i}")
            print(f"   set('key_{i}', 'value_{i}')")

        print(f"   Размер кэша: {cache.size()}")
        print(f"   Вытеснений: {cache.get_stats()['evictions']}")
        print()

        # Обращения к кэшу
        print("2. Обращения к элементам:")
        keys_to_access = ["key_0", "key_1", "key_2", "key_3"]
        for key in keys_to_access:
            val = cache.get(key)
            if val:
                print(f"   get('{key}') -> HIT: {val}")
            else:
                print(f"   get('{key}') -> MISS")

        print()

        # Добавление нового элемента
        print("3. Добавление нового элемента:")
        cache.set("key_new", "value_new")
        print("   set('key_new', 'value_new')")

        # Проверяем что осталось
        print("4. Проверка содержимого:")
        for key in ["key_1", "key_2", "key_3", "key_new"]:
            val = cache.get(key)
            print(f"   '{key}': {'есть' if val else 'удалён'}")

        # Статистика
        print("\n5. Статистика:")
        stats = cache.get_stats()
        for key, value in stats.items():
            if key == 'hit_rate':
                print(f"   {key}: {value:.2%}")
            else:
                print(f"   {key}: {value}")

        print("\n" + "=" * 50 + "\n")


def benchmark():
    """Сравнение производительности реализаций"""
    print("=== Performance Benchmark ===\n")

    sizes = [100, 1000, 10000]
    operations = 50000

    for size in sizes:
        print(f"Cache size: {size}")
        print("-" * 40)

        # OrderedDict реализация
        cache1 = LRUCache(size)
        start = time.time()

        for i in range(operations):
            cache1.set(f"key_{i % (size * 2)}", f"value_{i}")
            cache1.get(f"key_{i % (size * 2)}")

        time1 = time.time() - start
        stats1 = cache1.get_stats()

        # Doubly Linked List реализация
        cache2 = LRUCacheDoublyLinked(size)
        start = time.time()

        for i in range(operations):
            cache2.set(f"key_{i % (size * 2)}", f"value_{i}")
            cache2.get(f"key_{i % (size * 2)}")

        time2 = time.time() - start
        stats2 = cache2.get_stats()

        print(f"OrderedDict:")
        print(f"  Time: {time1:.4f}s")
        print(f"  Hit rate: {stats1['hit_rate']:.2%}")
        print(f"  Evictions: {stats1['evictions']}")

        print(f"Doubly Linked List:")
        print(f"  Time: {time2:.4f}s")
        print(f"  Hit rate: {stats2['hit_rate']:.2%}")
        print(f"  Evictions: {stats2['evictions']}")

        print(f"Speed ratio: {time2/time1:.2f}x\n")


def test_correctness():
    """Тест корректности работы"""
    print("=== Correctness Tests ===\n")

    def run_tests(cache_class, name):
        print(f"Testing {name}:")

        # Тест 1: Базовые операции
        cache = cache_class(2)
        cache.set("a", 1)
        cache.set("b", 2)
        assert cache.get("a") == 1, "Failed to get 'a'"

        cache.set("c", 3)  # Вытесняет 'b'
        assert cache.get("b") is None, "'b' should be evicted"
        assert cache.get("a") == 1, "'a' should still exist"
        assert cache.get("c") == 3, "'c' should exist"
        print("  ✓ Basic operations")

        # Тест 2: Обновление существующего ключа
        cache = cache_class(2)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("a", 10)  # Обновление
        cache.set("c", 3)   # Вытесняет 'b', а не 'a'
        assert cache.get("a") == 10, "'a' should be updated"
        assert cache.get("b") is None, "'b' should be evicted"
        print("  ✓ Update existing key")

        # Тест 3: Порядок LRU
        cache = cache_class(3)
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)

        cache.get("a")  # Делаем 'a' недавно использованным
        cache.set("d", 4)  # Должен вытеснить 'b'

        assert cache.get("a") == 1, "'a' should exist"
        assert cache.get("b") is None, "'b' should be evicted"
        assert cache.get("c") == 3, "'c' should exist"
        assert cache.get("d") == 4, "'d' should exist"
        print("  ✓ LRU order maintained")

        print(f"  All tests passed for {name}!\n")

    run_tests(LRUCache, "OrderedDict implementation")
    run_tests(LRUCacheDoublyLinked, "Doubly Linked List implementation")


if __name__ == "__main__":
    demo()
    benchmark()
    test_correctness()
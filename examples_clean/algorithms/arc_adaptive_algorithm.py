#!/usr/bin/env python3
"""
ARC (Adaptive Replacement Cache) - полная реализация

ARC динамически балансирует между LRU и LFU стратегиями,
адаптируясь к паттернам доступа к данным.
"""

from collections import OrderedDict
import time


class ARCCache:
    """Адаптивный заменяемый кэш"""

    def __init__(self, capacity):
        """
        Инициализация ARC кэша

        Args:
            capacity: Максимальный размер кэша
        """
        if capacity <= 0:
            raise ValueError("Capacity must be positive")

        self.c = capacity  # Общий размер кэша
        self.p = 0  # Целевой размер для T1 (адаптивный параметр)

        # T1, T2 - реальные кэши в памяти
        self.T1 = OrderedDict()  # Недавно использованные ОДИН раз
        self.T2 = OrderedDict()  # Недавно использованные МНОГОКРАТНО

        # B1, B2 - история удалённых ключей (ghost entries)
        self.B1 = OrderedDict()  # История из T1
        self.B2 = OrderedDict()  # История из T2

        # Статистика
        self.hits = 0
        self.misses = 0
        self.ghost_hits = 0

    def _replace(self, key):
        """Замена элемента при переполнении"""
        # Определяем из какого списка удалять
        if self.T1 and (
            len(self.T1) > self.p or
            (key in self.B2 and len(self.T1) == self.p)
        ):
            # Удаляем из T1
            old_key, _ = self.T1.popitem(last=False)
            self.B1[old_key] = None  # Добавляем в историю
        else:
            # Удаляем из T2
            old_key, _ = self.T2.popitem(last=False)
            self.B2[old_key] = None  # Добавляем в историю

    def _maintain_size(self):
        """Поддержание размера списков истории"""
        # Размер B1 + B2 не должен превышать 2c
        while len(self.B1) + len(self.B2) > 2 * self.c:
            if len(self.B1) > self.c:
                self.B1.popitem(last=False)
            else:
                self.B2.popitem(last=False)

    def get(self, key):
        """
        Получить значение по ключу

        Args:
            key: Ключ для поиска

        Returns:
            Значение или None если не найдено
        """
        if key in self.T1:
            # Перемещаем из T1 в T2 (повторное обращение)
            self.hits += 1
            value = self.T1.pop(key)
            self.T2[key] = value
            return value

        elif key in self.T2:
            # Обновляем позицию в T2
            self.hits += 1
            self.T2.move_to_end(key)
            return self.T2[key]

        # Cache miss
        self.misses += 1

        if key in self.B1:
            # Был в истории T1 - увеличиваем размер T1
            self.ghost_hits += 1
            delta = max(1, len(self.B2) // max(1, len(self.B1)))
            self.p = min(self.c, self.p + delta)
            self.B1.pop(key)

        elif key in self.B2:
            # Был в истории T2 - уменьшаем размер T1
            self.ghost_hits += 1
            delta = max(1, len(self.B1) // max(1, len(self.B2)))
            self.p = max(0, self.p - delta)
            self.B2.pop(key)

        return None

    def set(self, key, value):
        """
        Установить значение по ключу

        Args:
            key: Ключ
            value: Значение
        """
        if key in self.T1 or key in self.T2:
            # Ключ уже в кэше - обновляем
            if key in self.T1:
                self.T1[key] = value
                # Перемещаем в T2
                self.T1.pop(key)
                self.T2[key] = value
            else:
                self.T2[key] = value
                self.T2.move_to_end(key)
            return

        # Проверяем наличие в истории
        in_b1 = key in self.B1
        in_b2 = key in self.B2

        if in_b1 or in_b2:
            # Адаптация параметра p
            if in_b1:
                delta = max(1, len(self.B2) // max(1, len(self.B1)))
                self.p = min(self.c, self.p + delta)
                self.B1.pop(key)
            else:
                delta = max(1, len(self.B1) // max(1, len(self.B2)))
                self.p = max(0, self.p - delta)
                self.B2.pop(key)

            # Нужно освободить место
            if len(self.T1) + len(self.T2) >= self.c:
                self._replace(key)

            # Добавляем в T2
            self.T2[key] = value
        else:
            # Совсем новый ключ
            # Проверяем размер L1 = T1 + B1
            if len(self.T1) + len(self.B1) >= self.c:
                if len(self.T1) < self.c:
                    # Удаляем из B1
                    if self.B1:
                        self.B1.popitem(last=False)
                    # Замещаем
                    if len(self.T1) + len(self.T2) >= self.c:
                        self._replace(key)
                else:
                    # T1 полон, удаляем оттуда
                    old_key, _ = self.T1.popitem(last=False)
                    self.B1[old_key] = None
            else:
                # Проверяем общий размер
                total = len(self.T1) + len(self.B1) + len(self.T2) + len(self.B2)
                if total >= 2 * self.c:
                    # Удаляем из B2
                    if self.B2:
                        self.B2.popitem(last=False)

                # Замещаем если нужно
                if len(self.T1) + len(self.T2) >= self.c:
                    self._replace(key)

            # Добавляем в T1
            self.T1[key] = value

        # Поддерживаем размеры
        self._maintain_size()

    def clear(self):
        """Очистить кэш"""
        self.T1.clear()
        self.T2.clear()
        self.B1.clear()
        self.B2.clear()
        self.p = 0
        self.hits = 0
        self.misses = 0
        self.ghost_hits = 0

    def get_stats(self):
        """Получить статистику"""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0

        return {
            'hits': self.hits,
            'misses': self.misses,
            'ghost_hits': self.ghost_hits,
            'hit_rate': hit_rate,
            'p': self.p,
            'T1_size': len(self.T1),
            'T2_size': len(self.T2),
            'B1_size': len(self.B1),
            'B2_size': len(self.B2),
            'total_cached': len(self.T1) + len(self.T2)
        }


def demo():
    """Демонстрация работы ARC кэша"""
    print("=== ARC Cache Demo ===\n")

    # Создаём кэш размером 4
    cache = ARCCache(4)

    # Последовательный доступ (подходит для T1)
    print("1. Последовательный доступ:")
    for i in range(6):
        cache.set(f"seq_{i}", f"value_{i}")
        print(f"   set('seq_{i}', 'value_{i}')")

    stats = cache.get_stats()
    print(f"   T1: {stats['T1_size']}, T2: {stats['T2_size']}, p: {stats['p']:.2f}")
    print()

    # Повторный доступ (элементы переходят в T2)
    print("2. Повторный доступ к некоторым элементам:")
    for i in [3, 4, 5]:
        val = cache.get(f"seq_{i}")
        if val:
            print(f"   get('seq_{i}') -> HIT")
        else:
            cache.set(f"seq_{i}", f"value_{i}")
            print(f"   get('seq_{i}') -> MISS, set again")

    stats = cache.get_stats()
    print(f"   T1: {stats['T1_size']}, T2: {stats['T2_size']}, p: {stats['p']:.2f}")
    print()

    # Частый доступ к одним и тем же элементам
    print("3. Частый доступ к горячим данным:")
    hot_keys = ['hot_1', 'hot_2', 'hot_3']
    for _ in range(3):
        for key in hot_keys:
            val = cache.get(key)
            if not val:
                cache.set(key, f"hot_value_{key}")

    stats = cache.get_stats()
    print(f"   После 3 циклов обращений к горячим ключам:")
    print(f"   T1: {stats['T1_size']}, T2: {stats['T2_size']}, p: {stats['p']:.2f}")
    print()

    # Итоговая статистика
    print("4. Итоговая статистика:")
    stats = cache.get_stats()
    print(f"   Попадания: {stats['hits']}")
    print(f"   Промахи: {stats['misses']}")
    print(f"   Ghost попадания: {stats['ghost_hits']}")
    print(f"   Hit Rate: {stats['hit_rate']:.2%}")
    print(f"   Адаптивный параметр p: {stats['p']:.2f}")
    print(f"   Размер T1 (LRU-часть): {stats['T1_size']}")
    print(f"   Размер T2 (LFU-часть): {stats['T2_size']}")
    print(f"   Размер истории B1: {stats['B1_size']}")
    print(f"   Размер истории B2: {stats['B2_size']}")


def benchmark():
    """Сравнение производительности с разными паттернами доступа"""
    print("\n=== Benchmark: ARC vs Simple Patterns ===\n")

    capacity = 100
    data_size = 500

    # Последовательный доступ
    print("1. Sequential access pattern:")
    cache = ARCCache(capacity)
    start = time.time()

    for i in range(data_size):
        cache.set(f"key_{i}", f"value_{i}")

    for i in range(data_size):
        cache.get(f"key_{i}")

    elapsed = time.time() - start
    stats = cache.get_stats()
    print(f"   Time: {elapsed:.4f}s")
    print(f"   Hit rate: {stats['hit_rate']:.2%}")
    print(f"   Final p: {stats['p']:.2f}")
    print()

    # Случайный повторяющийся доступ (80/20)
    print("2. 80/20 access pattern (20% keys get 80% requests):")
    cache = ARCCache(capacity)
    import random

    # Генерируем горячие ключи
    hot_keys = [f"key_{i}" for i in range(int(data_size * 0.2))]
    cold_keys = [f"key_{i}" for i in range(int(data_size * 0.2), data_size)]

    # Заполняем кэш
    for key in hot_keys + cold_keys:
        cache.set(key, f"value_{key}")

    start = time.time()
    requests = 1000

    for _ in range(requests):
        if random.random() < 0.8:
            # 80% запросов к горячим ключам
            key = random.choice(hot_keys)
        else:
            # 20% запросов к холодным ключам
            key = random.choice(cold_keys)

        val = cache.get(key)
        if not val:
            cache.set(key, f"value_{key}")

    elapsed = time.time() - start
    stats = cache.get_stats()
    print(f"   Time: {elapsed:.4f}s")
    print(f"   Hit rate: {stats['hit_rate']:.2%}")
    print(f"   Final p: {stats['p']:.2f}")
    print(f"   T1/T2 ratio: {stats['T1_size']}/{stats['T2_size']}")


if __name__ == "__main__":
    demo()
    benchmark()
#!/usr/bin/env python3
"""
Comprehensive Cache Algorithms Benchmark

Сравнение всех реализованных алгоритмов кэширования на различных
паттернах доступа к данным.
"""

import time
import random
import statistics
from collections import defaultdict
import sys
import os

# Импортируем все наши алгоритмы
from arc_adaptive_algorithm import ARCCache
from lru_doubly_linked_list import LRUCache, LRUCacheDoublyLinked
from mru_most_recently_used import MRUCache
from lfu_least_frequently_used import LFUCache
from fifo_first_in_first_out import FIFOCache


class CacheBenchmark:
    """Комплексное тестирование алгоритмов кэширования"""

    def __init__(self, capacity=100, verbose=True):
        self.capacity = capacity
        self.verbose = verbose
        self.results = defaultdict(dict)

    def create_caches(self):
        """Создать все типы кэшей для тестирования"""
        return {
            'LRU (OrderedDict)': LRUCache(self.capacity),
            'LRU (Doubly Linked)': LRUCacheDoublyLinked(self.capacity),
            'MRU': MRUCache(self.capacity),
            'LFU': LFUCache(self.capacity),
            'ARC': ARCCache(self.capacity),
            'FIFO': FIFOCache(self.capacity)
        }

    def sequential_scan_test(self, data_size=1000, working_set_size=50):
        """
        Тест последовательного сканирования с рабочим набором

        Имитирует ситуацию когда есть стабильный рабочий набор,
        но иногда происходит сканирование большого объёма данных
        """
        if self.verbose:
            print("=== Sequential Scan Test ===")
            print(f"Capacity: {self.capacity}, Data size: {data_size}, Working set: {working_set_size}")

        caches = self.create_caches()

        for name, cache in caches.items():
            start_time = time.time()

            # Фаза 1: Заполняем рабочий набор
            working_set = [f"work_{i}" for i in range(working_set_size)]
            for key in working_set:
                cache.set(key, f"value_{key}")

            # Фаза 2: Обращаемся к рабочему набору
            for _ in range(100):
                key = random.choice(working_set)
                cache.get(key)

            # Фаза 3: Последовательное сканирование
            for i in range(data_size):
                cache.set(f"scan_{i}", f"scan_value_{i}")

            # Фаза 4: Проверяем сколько рабочего набора сохранилось
            preserved = sum(1 for key in working_set if cache.get(key) is not None)
            preservation_rate = preserved / len(working_set)

            elapsed = time.time() - start_time
            stats = cache.get_stats()

            # ARC кэш может не иметь поле evictions
            evictions = stats.get('evictions', 0)

            self.results['sequential_scan'][name] = {
                'time': elapsed,
                'hit_rate': stats['hit_rate'],
                'evictions': evictions,
                'preservation_rate': preservation_rate,
                'preserved_items': preserved
            }

            if self.verbose:
                print(f"  {name}:")
                print(f"    Time: {elapsed:.4f}s")
                print(f"    Hit rate: {stats['hit_rate']:.2%}")
                print(f"    Working set preserved: {preserved}/{len(working_set)} ({preservation_rate:.2%})")
                print(f"    Evictions: {evictions}")

    def zipf_distribution_test(self, requests=5000):
        """
        Тест с Zipf распределением (реалистичные паттерны доступа)

        80/20 правило: 20% ключей получают 80% запросов
        """
        if self.verbose:
            print("\n=== Zipf Distribution Test (80/20 rule) ===")
            print(f"Requests: {requests}")

        caches = self.create_caches()

        # Создаём ключи с Zipf распределением
        num_keys = self.capacity * 3
        keys = [f"key_{i}" for i in range(num_keys)]

        # Веса по закону Zipf (приблизительно 80/20)
        weights = []
        for i in range(num_keys):
            if i < num_keys // 5:  # Первые 20% ключей
                weights.append(4.0)  # Высокий вес
            else:
                weights.append(1.0)  # Низкий вес

        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]

        for name, cache in caches.items():
            start_time = time.time()

            for _ in range(requests):
                # Выбираем ключ с учётом весов
                r = random.random()
                cumsum = 0
                for i, w in enumerate(weights):
                    cumsum += w
                    if r < cumsum:
                        key = keys[i]
                        break

                val = cache.get(key)
                if not val:
                    cache.set(key, f"value_{key}")

            elapsed = time.time() - start_time
            stats = cache.get_stats()

            # ARC кэш может не иметь поле evictions
            evictions = stats.get('evictions', 0)

            self.results['zipf'][name] = {
                'time': elapsed,
                'hit_rate': stats['hit_rate'],
                'evictions': evictions
            }

            if self.verbose:
                print(f"  {name}:")
                print(f"    Time: {elapsed:.4f}s")
                print(f"    Hit rate: {stats['hit_rate']:.2%}")
                print(f"    Evictions: {evictions}")

    def temporal_locality_test(self, cycles=10, cycle_length=200):
        """
        Тест временной локальности

        Данные используются в циклах, имитируя периодический доступ
        """
        if self.verbose:
            print(f"\n=== Temporal Locality Test ===")
            print(f"Cycles: {cycles}, Cycle length: {cycle_length}")

        caches = self.create_caches()

        # Создаём несколько наборов данных
        sets = []
        for i in range(4):
            sets.append([f"set{i}_key_{j}" for j in range(self.capacity // 2)])

        for name, cache in caches.items():
            start_time = time.time()

            for cycle in range(cycles):
                # В каждом цикле используем разные наборы
                current_set = sets[cycle % len(sets)]

                for _ in range(cycle_length):
                    key = random.choice(current_set)
                    val = cache.get(key)
                    if not val:
                        cache.set(key, f"value_{key}")

            elapsed = time.time() - start_time
            stats = cache.get_stats()

            # ARC кэш может не иметь поле evictions
            evictions = stats.get('evictions', 0)

            self.results['temporal_locality'][name] = {
                'time': elapsed,
                'hit_rate': stats['hit_rate'],
                'evictions': evictions
            }

            if self.verbose:
                print(f"  {name}:")
                print(f"    Time: {elapsed:.4f}s")
                print(f"    Hit rate: {stats['hit_rate']:.2%}")
                print(f"    Evictions: {evictions}")

    def mixed_pattern_test(self, requests=3000):
        """
        Смешанный тест с разными паттернами доступа
        """
        if self.verbose:
            print(f"\n=== Mixed Pattern Test ===")
            print(f"Requests: {requests}")

        caches = self.create_caches()

        # Разные типы ключей
        hot_keys = [f"hot_{i}" for i in range(20)]           # Горячие данные
        warm_keys = [f"warm_{i}" for i in range(50)]         # Тёплые данные
        cold_keys = [f"cold_{i}" for i in range(200)]        # Холодные данные
        scan_keys = [f"scan_{i}" for i in range(1000)]       # Сканирование

        for name, cache in caches.items():
            start_time = time.time()

            for i in range(requests):
                # Выбираем паттерн доступа
                r = random.random()

                if r < 0.5:  # 50% - горячие данные
                    key = random.choice(hot_keys)
                elif r < 0.7:  # 20% - тёплые данные
                    key = random.choice(warm_keys)
                elif r < 0.9:  # 20% - холодные данные
                    key = random.choice(cold_keys)
                else:  # 10% - сканирование
                    key = random.choice(scan_keys)

                val = cache.get(key)
                if not val:
                    cache.set(key, f"value_{key}")

            elapsed = time.time() - start_time
            stats = cache.get_stats()

            # ARC кэш может не иметь поле evictions
            evictions = stats.get('evictions', 0)

            self.results['mixed_pattern'][name] = {
                'time': elapsed,
                'hit_rate': stats['hit_rate'],
                'evictions': evictions
            }

            if self.verbose:
                print(f"  {name}:")
                print(f"    Time: {elapsed:.4f}s")
                print(f"    Hit rate: {stats['hit_rate']:.2%}")
                print(f"    Evictions: {evictions}")

    def adaptive_pattern_test(self, phases=5, requests_per_phase=1000):
        """
        Тест адаптивности к изменениям паттернов

        Проверяет как алгоритмы адаптируются к смене рабочего набора
        """
        if self.verbose:
            print(f"\n=== Adaptive Pattern Test ===")
            print(f"Phases: {phases}, Requests per phase: {requests_per_phase}")

        caches = self.create_caches()

        for name, cache in caches.items():
            start_time = time.time()
            hit_rates_by_phase = []

            for phase in range(phases):
                # Каждая фаза имеет свой рабочий набор
                phase_keys = [f"phase{phase}_key_{i}" for i in range(self.capacity)]
                phase_hits = 0
                phase_total = 0

                for _ in range(requests_per_phase):
                    key = random.choice(phase_keys)
                    val = cache.get(key)

                    if val:
                        phase_hits += 1
                    else:
                        cache.set(key, f"value_{key}")

                    phase_total += 1

                phase_hit_rate = phase_hits / phase_total if phase_total > 0 else 0
                hit_rates_by_phase.append(phase_hit_rate)

            elapsed = time.time() - start_time
            stats = cache.get_stats()

            # Адаптивность = насколько быстро растёт hit rate в новых фазах
            adaptivity_score = statistics.mean(hit_rates_by_phase[1:]) if len(hit_rates_by_phase) > 1 else 0

            # ARC кэш может не иметь поле evictions
            evictions = stats.get('evictions', 0)

            self.results['adaptive'][name] = {
                'time': elapsed,
                'overall_hit_rate': stats['hit_rate'],
                'adaptivity_score': adaptivity_score,
                'phase_hit_rates': hit_rates_by_phase,
                'evictions': evictions
            }

            if self.verbose:
                print(f"  {name}:")
                print(f"    Time: {elapsed:.4f}s")
                print(f"    Overall hit rate: {stats['hit_rate']:.2%}")
                print(f"    Adaptivity score: {adaptivity_score:.2%}")
                print(f"    Phase hit rates: {[f'{rate:.1%}' for rate in hit_rates_by_phase]}")

    def run_all_tests(self):
        """Запустить все тесты"""
        print("🔥 Starting Comprehensive Cache Algorithm Benchmark")
        print("=" * 60)

        self.sequential_scan_test()
        self.zipf_distribution_test()
        self.temporal_locality_test()
        self.mixed_pattern_test()
        self.adaptive_pattern_test()

        print("\n" + "=" * 60)
        print("📊 BENCHMARK SUMMARY")
        print("=" * 60)

        self.print_summary()

    def print_summary(self):
        """Вывести сводные результаты"""

        # Собираем все алгоритмы
        all_algorithms = set()
        for test_results in self.results.values():
            all_algorithms.update(test_results.keys())

        # Таблица результатов
        print(f"{'Algorithm':<20} {'SeqScan':<8} {'Zipf':<8} {'Temporal':<9} {'Mixed':<8} {'Adaptive':<9} {'Avg':<8}")
        print("-" * 80)

        summary_scores = {}

        for algo in all_algorithms:
            scores = []
            row = f"{algo:<20}"

            # Sequential scan - важна preservation rate
            if algo in self.results['sequential_scan']:
                score = self.results['sequential_scan'][algo]['preservation_rate'] * 100
                scores.append(score)
                row += f"{score:>7.1f}%"
            else:
                row += f"{'N/A':>8}"

            # Zipf - hit rate
            if algo in self.results['zipf']:
                score = self.results['zipf'][algo]['hit_rate'] * 100
                scores.append(score)
                row += f"{score:>7.1f}%"
            else:
                row += f"{'N/A':>8}"

            # Temporal locality - hit rate
            if algo in self.results['temporal_locality']:
                score = self.results['temporal_locality'][algo]['hit_rate'] * 100
                scores.append(score)
                row += f"{score:>8.1f}%"
            else:
                row += f"{'N/A':>9}"

            # Mixed pattern - hit rate
            if algo in self.results['mixed_pattern']:
                score = self.results['mixed_pattern'][algo]['hit_rate'] * 100
                scores.append(score)
                row += f"{score:>7.1f}%"
            else:
                row += f"{'N/A':>8}"

            # Adaptive - adaptivity score
            if algo in self.results['adaptive']:
                score = self.results['adaptive'][algo]['adaptivity_score'] * 100
                scores.append(score)
                row += f"{score:>8.1f}%"
            else:
                row += f"{'N/A':>9}"

            # Average score
            if scores:
                avg_score = statistics.mean(scores)
                summary_scores[algo] = avg_score
                row += f"{avg_score:>7.1f}%"
            else:
                row += f"{'N/A':>8}"

            print(row)

        # Топ-3 алгоритма
        if summary_scores:
            print("\n🏆 TOP PERFORMERS:")
            sorted_algos = sorted(summary_scores.items(), key=lambda x: x[1], reverse=True)
            for i, (algo, score) in enumerate(sorted_algos[:3], 1):
                print(f"  {i}. {algo}: {score:.1f}%")

        # Рекомендации
        print("\n💡 RECOMMENDATIONS:")

        if 'sequential_scan' in self.results and self.results['sequential_scan']:
            best_seq_scan = max(self.results['sequential_scan'].items(),
                               key=lambda x: x[1]['preservation_rate'])
            print(f"  • For sequential scans with working set: {best_seq_scan[0]}")

        if 'zipf' in self.results and self.results['zipf']:
            best_zipf = max(self.results['zipf'].items(),
                           key=lambda x: x[1]['hit_rate'])
            print(f"  • For skewed access patterns (80/20): {best_zipf[0]}")

        if 'adaptive' in self.results and self.results['adaptive']:
            best_adaptive = max(self.results['adaptive'].items(),
                               key=lambda x: x[1]['adaptivity_score'])
            print(f"  • For changing patterns: {best_adaptive[0]}")


def quick_demo():
    """Быстрая демонстрация всех алгоритмов"""
    print("=== Quick Demo: All Cache Algorithms ===\n")

    capacity = 3
    caches = {
        'LRU': LRUCache(capacity),
        'MRU': MRUCache(capacity),
        'LFU': LFUCache(capacity),
        'ARC': ARCCache(capacity),
        'FIFO': FIFOCache(capacity)
    }

    # Общая последовательность операций
    operations = [
        ('set', 'a', 1),
        ('set', 'b', 2),
        ('set', 'c', 3),
        ('get', 'a', None),      # Увеличиваем частоту 'a'
        ('get', 'b', None),      # Увеличиваем частоту 'b'
        ('set', 'd', 4),         # Вытесняем кого-то
        ('set', 'e', 5),         # Вытесняем кого-то ещё
    ]

    for name, cache in caches.items():
        print(f"{name} Algorithm:")
        print("-" * 20)

        for op, key, value in operations:
            if op == 'set':
                cache.set(key, value)
                print(f"  set('{key}', {value})")
            else:  # get
                result = cache.get(key)
                print(f"  get('{key}') -> {'HIT' if result else 'MISS'}")

            # Показываем что в кэше
            if hasattr(cache, 'cache'):
                if hasattr(cache.cache, 'keys'):
                    keys = list(cache.cache.keys())
                else:
                    keys = list(cache.cache)
                print(f"    Cache contents: {keys}")

        stats = cache.get_stats()
        print(f"  Final hit rate: {stats['hit_rate']:.2%}")
        print()


if __name__ == "__main__":
    # Быстрая демонстрация
    quick_demo()

    print("\n" + "="*60)

    # Полное тестирование
    if len(sys.argv) > 1 and sys.argv[1] == '--full':
        benchmark = CacheBenchmark(capacity=100, verbose=True)
        benchmark.run_all_tests()
    else:
        # Краткое тестирование
        print("Running quick benchmark (use --full for comprehensive testing)")
        benchmark = CacheBenchmark(capacity=50, verbose=True)
        benchmark.zipf_distribution_test(requests=2000)
        benchmark.sequential_scan_test(data_size=300, working_set_size=25)
        benchmark.print_summary()
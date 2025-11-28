# Когда кэш бесполезен: размер данных

# Техномир: проверка размера рабочего набора
def should_use_cache(data_size_gb, cache_memory_gb):
    working_set_ratio = data_size_gb / cache_memory_gb

    if working_set_ratio > 10:
        # Рабочий набор в 10+ раз больше кэша
        return False, "Слишком большой рабочий набор"

    elif working_set_ratio > 3:
        # Только горячие данные
        return True, "Кэшировать только TOP-10% данных"

    else:
        # Весь набор помещается
        return True, "Можно кэшировать весь набор"

# Пример: каталог 1ТБ, кэш 16ГБ
# ratio = 64 → кэш бесполезен!
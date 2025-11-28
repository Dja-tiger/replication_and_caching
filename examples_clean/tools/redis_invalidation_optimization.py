# Redis: оптимизация инвалидации

# Lua-скрипт для атомарной инвалидации по тегам
lua_delete_by_tag = """
local tag_key = KEYS[1]
local keys = redis.call('SMEMBERS', tag_key)

if #keys > 0 then
    redis.call('DEL', unpack(keys))
end

redis.call('DEL', tag_key)
return #keys
"""

# Регистрируем скрипт
delete_by_tag_script = redis.register_script(lua_delete_by_tag)

# Используем
deleted_count = delete_by_tag_script(keys=[f"tag:{tag}"])

# Pipeline для массовой инвалидации
def bulk_invalidate(keys_to_delete):
    pipe = redis.pipeline()
    for key in keys_to_delete:
        pipe.delete(key)
    pipe.execute()

# Асинхронная инвалидация через задачи
def async_invalidate(tag):
    celery_task.delay('invalidate_by_tag', tag)
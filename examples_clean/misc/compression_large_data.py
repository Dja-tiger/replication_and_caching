# 7. Compression для больших данных

import zlib
import pickle

class CompressedCache:
    def set(self, key, value, compress_threshold=1024):
        serialized = pickle.dumps(value)

        if len(serialized) > compress_threshold:
            # Сжимаем большие объекты
            compressed = zlib.compress(serialized, level=1)
            self.redis.set(f"{key}:z", compressed)
            self.redis.set(f"{key}:meta", "compressed")
        else:
            self.redis.set(key, serialized)

    def get(self, key):
        if self.redis.get(f"{key}:meta") == "compressed":
            compressed = self.redis.get(f"{key}:z")
            serialized = zlib.decompress(compressed)
        else:
            serialized = self.redis.get(key)

        return pickle.loads(serialized) if serialized else None
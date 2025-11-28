# Memcached: консистентное хеширование (1/2)

# Клиент с consistent hashing для Техномира
import hashlib
from bisect import bisect_right

class ConsistentHashMemcache:
    def __init__(self, servers, virtual_nodes=150):
        self.servers = servers
        self.virtual_nodes = virtual_nodes
        self.ring = {}
        self.sorted_keys = []
        self._build_ring()

    def _hash(self, key):
        return int(hashlib.md5(key.encode()).hexdigest(), 16)
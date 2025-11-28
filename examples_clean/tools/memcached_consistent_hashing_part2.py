# Memcached: консистентное хеширование (2/2)

def _build_ring(self):
        for server in self.servers:
            for i in range(self.virtual_nodes):
                virtual_key = f"{server}:{i}"
                hash_value = self._hash(virtual_key)
                self.ring[hash_value] = server
        self.sorted_keys = sorted(self.ring.keys())

    def get_server(self, key):
        if not self.ring:
            return None
        hash_value = self._hash(key)
        idx = bisect_right(self.sorted_keys, hash_value)
        return self.ring[self.sorted_keys[idx % len(self.sorted_keys)]]
# Redis Master-Replica

# redis-master.conf
port 6379
requirepass "strongpass"
masterauth "strongpass"
maxmemory 4gb
maxmemory-policy allkeys-lru

# redis-replica.conf
port 6380
replicaof master.redis 6379
masterauth "strongpass"
requirepass "strongpass"
replica-read-only yes
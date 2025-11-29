CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD 'replicate_me';
CREATE ROLE readonly WITH LOGIN PASSWORD 'readonly_password';

GRANT pg_read_all_data TO readonly;

-- Demo table for load tests
CREATE TABLE IF NOT EXISTS public.users (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

INSERT INTO public.users (name, email)
SELECT 'User ' || g, 'user' || g || '@example.com'
FROM generate_series(1, 2000) AS g;

-- Pre-create replication slots for deterministic names
SELECT * FROM pg_create_physical_replication_slot('replica1_slot');
SELECT * FROM pg_create_physical_replication_slot('replica2_slot');

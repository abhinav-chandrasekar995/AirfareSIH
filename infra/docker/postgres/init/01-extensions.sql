-- TimescaleDB is provided by the base image; the migration creates hypertables.
-- On Supabase / plain Postgres this file is not used and the migration degrades
-- hypertables to ordinary tables automatically.
CREATE EXTENSION IF NOT EXISTS timescaledb;

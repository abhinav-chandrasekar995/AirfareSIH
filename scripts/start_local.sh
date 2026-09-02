#!/usr/bin/env bash
# No-Docker portable start. Assumes a reachable Postgres (local or Supabase via
# DATABASE_URL) and optionally Redis. Runs migrations, loads the seed, starts the API.
set -e
cd "$(dirname "$0")/../backend"
echo ">> migrating"
alembic upgrade head
echo ">> seeding"
python -m seeds.load_seed
echo ">> starting API on :8000"
uvicorn app.main:app --host 0.0.0.0 --port 8000

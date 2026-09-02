# Working on India Airfare Intelligence

This gets you from a fresh clone to the exact same working state the rest of the team
sees — running app, populated database, working tests, direct table access if you want
it. If something here is out of date, fix it in the same PR as whatever you were doing
when you noticed.

## 1. Prerequisites

- **Docker + Docker Compose** (recommended path — this is the only thing you need).
- If you'd rather run without Docker: **Python 3.11+**, **Node 20+**, and a local
  **PostgreSQL 16+** (TimescaleDB extension is optional — the schema degrades to plain
  tables/indexes automatically if it's not installed).

## 2. Get it running

```bash
git clone <repo-url>
cd AirfareSIH
cp .env.example .env
docker compose up --build
```

That single command brings up Postgres, Redis, the API, the Celery worker/beat, and the
frontend — runs migrations, and loads a **deterministic ~120k-observation seed dataset**
automatically. No external network access is required (`data_mode = REPLAY`, shown as a
badge in the UI).

Open:
- **Frontend** — http://localhost:3000
- **API docs (OpenAPI)** — http://localhost:8000/api/docs

Watch the `backend` container's logs for a block like this, printed once:

```
Seed load complete. Demo API keys (shown once):
  ADMIN    iai_xxxxxxxx.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  ANALYST  iai_xxxxxxxx.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  PUBLIC   iai_xxxxxxxx.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Save these somewhere** (a password manager, not a commit) — they are hashed in the
database and cannot be recovered once the terminal scrolls past them. They're unique to
your machine; nobody else's keys will work against your local instance and vice versa.

Without Docker, the equivalent is:

```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate   # .venv\Scripts\activate on Windows
pip install -r requirements-dev.txt
cp .env.example .env    # DATABASE_URL already defaults to the local Postgres below
alembic upgrade head
python -m seeds.load_seed     # prints the same kind of demo-key block above
uvicorn app.main:app --reload --port 8000

# frontend, separate terminal
cd frontend
npm install
npm run dev
```

## 3. Actually seeing the data

Three ways, in increasing order of "raw":

**a) The app itself** — dashboard, routes, anomalies, backtesting, etc. at
`localhost:3000`. Most pages work with no key (`PUBLIC` access). A handful of
features — the fares CSV export in Data Explorer, and anything under `/api-portal` that
needs elevated access — need a key pasted in at **`/api-portal/keys`**: paste one of the
keys from your terminal, click Save, and it's stored in that browser's `localStorage`
(sent only to this app's own API, nowhere else) as either ANALYST or ADMIN depending on
which key you used.

**b) The API directly** — `/api-portal` in the app lists every endpoint with a
copy-pasteable `curl` example; full schema at `localhost:8000/api/docs`. Example:

```bash
curl -H "X-API-Key: YOUR_KEY" "http://localhost:8000/api/v1/dashboard"
```

**c) The raw Postgres tables** — `docker-compose.yml` exposes Postgres on
`localhost:5432` with the credentials from `.env.example` (`airfare` / `airfare` /
database `airfare` — a fixed local-only default, not a real secret). Connect with `psql`
or any GUI client (pgAdmin, DBeaver, TablePlus, etc.):

```bash
psql "host=localhost port=5432 dbname=airfare user=airfare password=airfare"
```

**Row Level Security is enforced at the database itself** (not just the API layer) — a
plain `SELECT` with no role set will come back empty or fail on most tables by design
(fail-closed, not a bug). To see everything as an admin in a `psql` session:

```sql
SET app.role = 'ADMIN';
SELECT * FROM scrape_runs;
```

`app.role` accepts `PUBLIC`, `ANALYST`, or `ADMIN` and only affects the current session —
it does not persist across a new connection, so you'll need to `SET` it again each time
you reconnect.

## 4. Running the tests

```bash
cd backend && pytest -q          # unit + golden tests need no DB; more run once TEST_DATABASE_URL is set
cd frontend && npm run test      # component/accessibility tests (vitest)
cd frontend && npm run e2e       # Playwright, including the network-off resilience path
cd frontend && npx tsc --noEmit  # typecheck
```

Before pushing anything nontrivial, also do a clean build once (stop the dev server
first, since `next build` and `next dev` can't run against the same `.next/` output at
once):

```bash
cd frontend && npm run build
```

## 5. Making changes

- **Schema changes** go through Alembic — add a migration under `backend/alembic/versions/`,
  never hand-edit an existing one. After pulling someone else's migration:
  `cd backend && alembic upgrade head`.
- **Seed data** is fully regenerated from code (`backend/seeds/generate_seed.py` +
  `load_seed.py`), not committed as a data file. If you change the seed generator,
  everyone's local data changes too the next time they reload it
  (`make seed` / `python -m seeds.load_seed`) — mention that in your PR.
- **`app/analytics/` must stay pure** — no imports from `db`, `api`, `collection`,
  `services`, or `tasks`. This is enforced in CI by `lint-imports`
  (`make lint` runs it locally too); it's what keeps every published statistic
  reproducible outside the API.
- **Log the decision, not just the diff.** [`IMPLEMENTATION_LOG.md`](IMPLEMENTATION_LOG.md)
  is the running record of every nontrivial choice made on this project and why — bugs
  found, tradeoffs taken, things deliberately left as-is. Add an entry there for anything
  a future contributor would otherwise have to reverse-engineer from a commit message.

## 6. Common gotchas

- **RLS fails closed.** If an endpoint or query returns emptier than you expect, check
  whether the right `app.role` is actually being set for that request/session before
  assuming the data is missing — see §3(c) above. This has bitten this project more than
  once; see `IMPLEMENTATION_LOG.md` for the full story.
- **Windows + asyncpg**: if you're on Windows and hit an event-loop-related asyncpg
  error, it's the ProactorEventLoop/SelectorEventLoop mismatch — already worked around in
  this codebase, but worth knowing if you ever see it resurface after a dependency bump.
- **`docker compose up` gives everyone their own database**, not a shared one — cloning
  the repo does not connect you to anyone else's data. If you specifically want a shared
  instance the whole team writes to, see the Supabase section in `README.md`.

## 7. Where to look next

- [`README.md`](README.md) — stack, repo layout, quick start.
- [`IMPLEMENTATION_LOG.md`](IMPLEMENTATION_LOG.md) — the "why" behind everything.
- [`doc/`](doc/) — PRD, architecture, design system, schema, folder structure.
- [`Build Prompt — INDIA AIRFARE INTELLIGENCE.md`](<Build Prompt — INDIA AIRFARE INTELLIGENCE.md>) — the original build spec this was built against.

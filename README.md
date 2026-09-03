# India Airfare Intelligence

**Real-Time Airfare Price Index & CPI Augmentation Platform** — a statistical intelligence platform for India's domestic aviation market, built for an SIH problem statement. Not a flight-booking site.

> Collect → Clean → Measure → Explain → Validate → Predict → Augment

Full requirements, architecture and design rationale live in [`doc/`](doc/) and the build spec in [`Build Prompt — INDIA AIRFARE INTELLIGENCE.md`](<Build Prompt — INDIA AIRFARE INTELLIGENCE.md>). **Every implementation decision made while building this is logged in [`IMPLEMENTATION_LOG.md`](IMPLEMENTATION_LOG.md)** — read it if you want the "why," not just the "what."

**Cloning this to work on it?** [`CONTRIBUTING.md`](CONTRIBUTING.md) covers everything beyond the quick start below — seeing the data three different ways (app, API, raw Postgres), running the tests, the migration/seed workflow, and known gotchas.

## Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router) · TypeScript · Tailwind CSS · TanStack Query · Zustand · ECharts |
| Backend | Python · FastAPI · Pydantic v2 · SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 16 (+ TimescaleDB where available) with Row Level Security |
| Cache / queue | Redis · Celery + Celery Beat |
| Infra | Docker Compose (portable local) · Supabase (shared team Postgres) |

## Quick start — portable local (recommended, works offline)

Download docker desktop
Restart system 
Run docker desktop 

```bash
cp .env.example .env
docker compose up --build
```

for later runs, 
```bash
docker compose up -d
```

This brings up Postgres (TimescaleDB image), Redis, the API, workers, and the frontend, runs migrations, and **loads a deterministic 120k-observation seed dataset** automatically. Open:

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/api/docs

The demo runs entirely on seeded data (`data_mode = REPLAY`, shown in the UI badge) — no external network access is required, so it keeps working if judging-day wifi does not.

## Quick start — no Docker (local Postgres or Supabase)

```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements-dev.txt
cp .env.example .env   # set DATABASE_URL to your Postgres or Supabase connection string
alembic upgrade head
python -m seeds.load_seed     # prints demo API keys once — save them
uvicorn app.main:app --reload --port 8000

# frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### Using Supabase (shared database for teammates)

1. Create a Supabase project → Project Settings → Database → Connection string → **Session pooler** (URI).
2. Set `DATABASE_URL` in `backend/.env` to that string, with the driver prefix changed to `postgresql+asyncpg://`.
3. Run `alembic upgrade head` then `python -m seeds.load_seed` once.
4. Share the Supabase project (not raw credentials) with teammates; each of you points your own `frontend/.env.local` `NEXT_PUBLIC_API_BASE_URL` at whichever backend instance you're running against that shared DB.

Supabase supports Postgres Row Level Security natively, so the RLS policies in `backend/alembic/versions/0001_initial_schema.py` apply unchanged there.

## Repository layout

```
backend/    FastAPI + Celery + the pure analytics engine (app/analytics/ has zero DB/API deps)
frontend/   Next.js App Router, all 13 app pages + marketing site
infra/      Docker, Postgres init, Grafana dashboards, optional k8s
doc/        PRD, architecture, design system, backend schema, folder structure
scripts/    Dev/ops helper scripts
```

See [`doc/05-FOLDER-STRUCTURE.md`](doc/05-FOLDER-STRUCTURE.md) for the full tree with a purpose note per directory.

## Testing

```bash
cd backend && pytest -q          # 79 unit + 3 golden tests run with no DB; 14 more run once TEST_DATABASE_URL is set
cd frontend && npm run test      # 28 component/accessibility tests
cd frontend && npm run e2e       # Playwright, incl. the network-off demo-resilience path
```

## Key architectural guarantees

- **The API never triggers scraping.** Collection is scheduled and asynchronous; the read path only ever serves precomputed data.
- **`app/analytics/` is pure.** No imports from `db`, `api`, `collection`, `services` or `tasks` — enforced in CI by `lint-imports`. This is what makes every published statistic reproducible.
- **RLS is enforced at the database**, not just the API layer — a missing role setting fails closed.
- **The CPI simulator's disclaimer cannot be omitted or dismissed** — enforced by both the analytics layer and a response middleware.
- **A point forecast is never rendered without its prediction interval** — enforced at the Pydantic schema and the React component's type signature.
- **Ethical collection safeguards** (robots.txt, rate limits, circuit breaking, challenge detection) live in the adapter base class and cannot be bypassed by an individual adapter.

Full rationale for all of the above — and the bugs found and fixed along the way — is in [`IMPLEMENTATION_LOG.md`](IMPLEMENTATION_LOG.md).

## License

MIT — see [`LICENSE`](LICENSE).

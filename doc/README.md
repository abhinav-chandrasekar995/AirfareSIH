# India Airfare Intelligence — Documentation

Source spec: `../INDIA AIRFARE INTELLIGENCE (1).md`

| Doc | Contents |
|---|---|
| [01-PRD.md](01-PRD.md) | Problem statement, personas, all 16 module requirements (P0/P1/P2), NFRs, demo-resilience requirements, release plan, risks, success metrics |
| [02-ARCHITECTURE.md](02-ARCHITECTURE.md) | C4 context/container views, the 7-stage pipeline (Collect→Clean→Measure→Explain→Validate→Predict→Augment), backend layering, async processing, security, ethical-scraping architecture, ADRs |
| [03-DESIGN.md](03-DESIGN.md) | Design tokens (colour/type/spacing), component specs, per-screen layouts for every module, accessibility, component inventory |
| [04-BACKEND-SCHEMA.md](04-BACKEND-SCHEMA.md) | Full PostgreSQL + TimescaleDB DDL, continuous aggregates, retention policy, seed strategy, API contract |
| [05-FOLDER-STRUCTURE.md](05-FOLDER-STRUCTURE.md) | Complete `backend/`, `frontend/`, `infra/` trees with purpose notes and a directory-to-requirement map |

**Stack:** React (Next.js) + TypeScript · FastAPI (Python) · PostgreSQL 16 + TimescaleDB · Redis · Celery · Docker.

Read in order (PRD → Architecture → Design → Schema → Folder Structure) — each doc cross-references the others.

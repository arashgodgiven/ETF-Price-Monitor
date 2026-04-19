# ETF Price Monitor

A full-stack single-page application that allows traders to view historical prices and top holdings for a given ETF.

Built for the **BMO Capital Markets — Data Cognition Team** full-stack developer interview assessment.

---

## Quick Start

```bash
# 1. Clone and enter the project
git clone <repo-url> && cd etf-monitor

# 2. Copy environment config
cp .env.example .env

# 3. Start the full stack (DB seeds automatically on first run)
docker compose up --build

# 4. Open the app
open http://localhost:80

# API docs available at:
open http://localhost:8000/api/docs
```

> **First boot note:** TimescaleDB needs ~10 seconds to initialize before the seed script runs. The backend waits for a healthy DB before starting (see `depends_on` healthcheck in `docker-compose.yml`).

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Browser                                                        │
│  React 18 + Redux Toolkit + RTK Query + Recharts                │
└───────────────────────┬─────────────────────────────────────────┘
                        │  HTTP (nginx reverse proxy)
┌───────────────────────▼─────────────────────────────────────────┐
│  Backend                                                        │
│  FastAPI + asyncpg + SQLAlchemy (async)                         │
│  ┌──────────┐  ┌─────────────┐  ┌──────────────────────────┐    │
│  │  Routers │→ │ETF Service  │→ │  TimescaleDB (Postgres)  │    │
│  │(HTTP only│  │(logic only) │  │  prices hypertable       │    │
│  └──────────┘  └─────────────┘  │  etfs + constituents     │    │
└─────────────────────────────────└───────────────────────────────┘
```

### Why these technology choices?

**TimescaleDB over InfluxDB**
Prices are inherently relational — every ETF price query requires joining `prices` with `etf_constituents` to compute weighted sums. TimescaleDB gives us a full SQL engine (PostgreSQL) with time-series partitioning on top. InfluxDB's query model (Flux) fights relational joins and would complicate every core query. At true scale (tick-level data, millions of rows/day), TimescaleDB's hypertable partitioning handles it without re-platforming.

**FastAPI over Flask/Django**
Native async (no thread-pool workarounds), automatic OpenAPI docs, and first-class Pydantic integration for request/response validation. The async session pool (`asyncpg`) means a single worker can handle many concurrent requests under I/O load — important when the service eventually fans out to multiple data sources.

**SQLAlchemy async over raw asyncpg**
Keeps queries portable and testable. The repository pattern means swapping TimescaleDB for another store is a one-layer change. Raw asyncpg would bleed DB-specific syntax everywhere.

**Redux Toolkit + RTK Query over Context/`useEffect`**
RTK Query gives us server state management with built-in caching, deduplication, and cache invalidation — the kind of thing teams spend months reinventing with raw `useEffect`. When a new ETF is uploaded, the session list invalidates and refetches automatically. Zero manual state synchronization.

**Anonymous sessions over no persistence**
Uploads stored in-memory die on pod restart and can't cross horizontal scaling boundaries. A `session_id` UUID cookie scoped to `etfs` rows is the minimum viable persistence layer. When auth is added, `session_id` becomes a FK to `users` — no schema migration beyond adding a column.

---

## Project Structure

```
etf-monitor/
├── backend/
│   ├── app/
│   │   ├── main.py               # App factory, middleware, lifespan hooks
│   │   ├── config.py             # Pydantic Settings — all config from env vars
│   │   ├── core/
│   │   │   ├── database.py       # Async engine + session factory
│   │   │   ├── exceptions.py     # Exception hierarchy + FastAPI handlers
│   │   │   └── logging.py        # Structured JSON logging (prod) / pretty (dev)
│   │   ├── routers/
│   │   │   ├── etf.py            # HTTP layer only — no business logic
│   │   │   └── health.py         # /api/v1/health — DB liveness included
│   │   ├── services/
│   │   │   └── etf_service.py    # All domain logic — independently testable
│   │   └── models/
│   │       └── schemas.py        # Pydantic request/response contracts
│   └── tests/
│       └── test_etf_service.py   # Service unit tests (no DB required)
│
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── store.ts          # Redux store
│       │   └── hooks.ts          # Typed useAppDispatch / useAppSelector
│       ├── features/etf/
│       │   ├── etfApiSlice.ts    # RTK Query — all API endpoints
│       │   └── etfSlice.ts       # UI state (selected ETF)
│       ├── components/
│       │   ├── FileUpload/       # Drag-and-drop CSV uploader
│       │   ├── HoldingsTable/    # Constituents with latest prices
│       │   ├── PriceChart/       # Zoomable area chart (click-drag to zoom)
│       │   ├── TopHoldingsChart/ # Bar chart — top 5 by holding size
│       │   └── Layout/           # Sidebar + Dashboard shell
│       ├── types/etf.ts          # Shared TypeScript interfaces
│       └── utils/formatters.ts   # Currency, percent, date formatters
│
└── db/
    └── init/
        ├── 01_schema.sql         # Schema + hypertable creation (idempotent)
        └── 02_seed.sql           # Unpivots prices.csv wide→long, seeds once
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/health` | Service + DB health check |
| `POST` | `/api/v1/etf/upload` | Upload ETF CSV; returns parsed summary |
| `GET` | `/api/v1/etf/session` | All ETFs uploaded in this session |
| `GET` | `/api/v1/etf/{id}` | ETF summary with constituents + latest prices |
| `GET` | `/api/v1/etf/{id}/price-history` | Reconstructed price time series (`?date_from=&date_to=`) |
| `GET` | `/api/v1/etf/{id}/top-holdings` | Top N by holding size (`?limit=5`) |

Full interactive docs at `http://localhost:8000/api/docs`.

---

## ETF Price Calculation

The reconstructed ETF price at time `t` is:

```
ETF_price(t) = Σ weight_i × price_i(t)
```

This is computed in a single SQL aggregation query:

```sql
SELECT p.date, SUM(ec.weight * p.close_price) AS etf_price
FROM etf_constituents ec
JOIN prices p ON p.stock_name = ec.stock_name
WHERE ec.etf_id = :etf_id
GROUP BY p.date
ORDER BY p.date ASC
```

No Python-side aggregation — pushed entirely to the database.

---

## Assumptions

1. **Weights are static over time.** The spec states this explicitly — weight columns in ETF CSVs apply uniformly across all historical dates.
2. **Prices CSV is the authoritative source** for all known stock names. Uploading an ETF with an unknown stock_name is rejected with a `422` error.
3. **Weight validation:** Each weight must be `> 0` and `≤ 1`. Weights don't need to sum exactly to 1.0 (floating-point rounding in the provided files makes strict enforcement unreliable).
4. **No authentication.** Users are identified by an anonymous `session_id` cookie. This is a deliberate design choice — the session system is structured so adding JWT auth requires changing only the `get_or_create_session` dependency in `routers/etf.py`.
5. **Single deployment unit.** All services run in Docker Compose. The architecture supports extraction into separate deployable microservices (the backend has no internal coupling between components).

---

## Design Decisions for Scale

| Concern | Current | Path to scale |
|---------|---------|---------------|
| DB reads | Single Postgres instance | Read replicas behind a connection pooler (PgBouncer) |
| Price history queries | Hypertable range scan | Add `stock_name` chunk index; partition by month |
| Horizontal scaling | Single backend pod | Stateless FastAPI — scale with `docker compose --scale backend=N` or K8s HPA |
| Session state | DB-backed cookie | Swap `get_or_create_session` dep for JWT — no other changes |
| Price data source | Seeded CSV | Replace `02_seed.sql` with a market data ingestion job (e.g. Kafka consumer) |
| Logging | Structured JSON to stdout | Ship to Datadog / CloudWatch via log driver — no code changes needed |

---

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

Tests cover CSV validation edge cases at the service layer — no DB required.

---

## Development (without Docker)

```bash
# Backend
cd backend
pip install -r requirements.txt
DATABASE_URL=postgresql+asyncpg://etf_user:etf_password@localhost:5432/etf_monitor \
  uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev   # proxies /api to localhost:8000 via vite.config.ts
```

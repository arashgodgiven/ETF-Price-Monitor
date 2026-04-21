# ETF Price Monitor

A full-stack single-page application that allows traders to upload ETF definitions, view reconstructed historical price performance, analyze top holdings, and interactively explore constituent data.

Built for the **BMO Capital Markets — Data Cognition Team** full-stack developer interview assessment.

---

## 🚀 Live Demo

**[https://etf-price-monitor.vercel.app](https://etf-price-monitor.vercel.app)**

Upload `ETF1.csv` or `ETF2.csv` from the `db/` folder to get started.

---

## Features

### Core Requirements
- Upload an ETF CSV file containing constituent names and weights
- Interactive table displaying constituents with name, weight, and latest closing price
- Zoomable time series chart of the reconstructed ETF price history (click-drag to zoom)
- Bar chart displaying the top 5 holdings by holding size (weight × latest price)

### Table Enhancements
- **Sort by column** — click any column header to sort ascending / descending / reset
- **Per-column search** — magnifier icon on each header reveals a search input; text search on stock name, range filter (min/max) on weight and price
- **Hide column** — eye icon toggles column visibility without changing table width
- **Drag to reorder** — drag handle on each row to manually reorder constituents; resets active sort
- **Double-click row** — switches price chart to show price history for that individual stock

### Charts
- **ETF price chart** — zoomable area chart with click-drag zoom and reset
- **Individual stock price chart** — double-click any bar in Top Holdings or any row in the table to view that stock's price history; "← Back to ETF" button returns to ETF view
- **Auto-scroll** — page scrolls to price chart automatically when a stock is selected

### Dashboard
- **ETF header banner** — displays ETF name, date range, latest price, highest price, and lowest price over the period
- **Session management** — uploaded ETFs persist in the sidebar for the session; click to switch between ETFs
- **Delete ETF** — hover over any ETF in the sidebar to reveal a trash icon; confirms before deleting

### UX Details
- Hover hints on stock names and chart bars: "Double-click to view price history"
- Hover hint on drag handles: "Drag to reorder"
- Filter status bar shows "Showing X of Y holdings" with a clear all button when filters are active
- Sticky table header — header stays fixed while scrolling through constituents
- Table scrolls internally — card height stays fixed regardless of filter results

---

## Quick Start (Local)

```bash
# 1. Clone and enter the project
git clone https://github.com/arashgodgiven/ETF-Price-Monitor.git
cd ETF-Price-Monitor

# 2. Copy environment config
cp .env.example .env

# 3. Start the full stack (DB seeds automatically on first run)
docker compose up --build

# 4. Open the app
open http://localhost:80

# API docs available at:
open http://localhost:8000/api/docs
```

> **First boot note:** The database needs ~10 seconds to initialize before the seed script runs. The backend waits for a healthy DB before starting (see `depends_on` healthcheck in `docker-compose.yml`).

---

## Production Deployment

| Service | Platform | URL |
|---------|----------|-----|
| Frontend | Vercel | https://etf-price-monitor.vercel.app |
| Backend | Render | https://etf-price-monitor.onrender.com |
| Database | Render Postgres | Internal to Render network |

> **Note:** The backend runs on Render's free tier and may take 30–60 seconds to wake up after inactivity. The first request after a cold start will be slow — subsequent requests are fast.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Browser                                                    │
│  React 18 + Redux Toolkit + RTK Query + Recharts + dnd-kit  │
└───────────────────────┬─────────────────────────────────────┘
                        │  HTTPS
┌───────────────────────▼─────────────────────────────────────┐
│  Backend (Render)                                           │
│  FastAPI + asyncpg + SQLAlchemy (async)                     │
│  ┌──────────┐  ┌─────────────┐  ┌──────────────────────┐    │
│  │  Routers │→ │ETF Service  │→ │  Repository          │    │
│  │(HTTP only│  │(logic only) │  │  (SQL only)          │    │
│  └──────────┘  └─────────────┘  └───────────┬──────────┘    │
└─────────────────────────────────────────────┼───────────────┘
                                              │     
┌─────────────────────────────────────────────▼───────────────┐
│  Database (Render Postgres)                                 │
│  prices · etfs · etf_constituents                           │
└─────────────────────────────────────────────────────────────┘
```

### Why these technology choices?

**Local development:** TimescaleDB (Postgres extension) with hypertable partitioning on the prices table

**Production:** Standard Postgres on Render free tier — TimescaleDB not available on managed free-tier Postgres. At current data scale (2,600 rows) there is no performance difference. The natural upgrade path is Timescale Cloud when the dataset grows to millions of rows.

**FastAPI over Flask/Django**
Native async, automatic OpenAPI docs, and first-class Pydantic integration. The async session pool (`asyncpg`) means a single worker handles many concurrent requests under I/O load.

**Repository pattern**
All SQL lives in `etf_repository.py`. The service layer contains zero raw queries. Swapping the DB engine is a one-file change.

**SQLAlchemy async over raw asyncpg**
Keeps queries portable and testable. Named `:param` bindings make SQL injection impossible by construction.

**Redux Toolkit + RTK Query over Context/`useEffect`**
Built-in caching, deduplication, and declarative cache invalidation. When a new ETF is uploaded, `invalidatesTags: ["Session"]` causes the sidebar to refetch automatically — zero manual state synchronization.

**Anonymous session cookies**
A `session_id` UUID cookie scoped to `etfs` rows is the minimum viable persistence layer. When auth is added, `session_id` becomes a FK to `users` — the only required change is swapping the `get_or_create_session` dependency in `routers/etf.py`.

---

## Project Structure

```
ETF-Price-Monitor/
├── backend/
│   ├── app/
│   │   ├── main.py                    # App factory, middleware, lifespan hooks
│   │   ├── config.py                  # Pydantic Settings — all config from env vars
│   │   ├── core/
│   │   │   ├── database.py            # Async engine + session factory
│   │   │   ├── exceptions.py          # Exception hierarchy + FastAPI handlers
│   │   │   └── logging.py             # Structured JSON logging (prod) / pretty (dev)
│   │   ├── routers/
│   │   │   ├── etf.py                 # HTTP layer only — session cookie, route handlers
│   │   │   └── health.py              # /api/v1/health — DB liveness check
│   │   ├── services/
│   │   │   └── etf_service.py         # All domain logic — independently testable
│   │   ├── repositories/
│   │   │   └── etf_repository.py      # All SQL — no business logic
│   │   └── models/
│   │       ├── etf_summary_schema.py
│   │       ├── etf_price_history_schema.py
│   │       ├── etf_top_holdings_schema.py
│   │       ├── constituent_schema.py
│   │       ├── price_point_schema.py
│   │       ├── top_holding_schema.py
│   │       └── health_schema.py
│   └── tests/
│       └── test_etf_service.py        # Service unit tests (no DB required)
│
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── store.ts               # Redux store
│       │   └── hooks.ts               # Typed useAppDispatch / useAppSelector
│       ├── features/etf/
│       │   ├── etfApiSlice.ts         # RTK Query — all API endpoints + cache tags
│       │   └── etfSlice.ts            # UI state (selected ETF, selected stock)
│       ├── components/
│       │   ├── FileUpload/            # Drag-and-drop CSV uploader
│       │   ├── HoldingsTable/         # Sortable, filterable, draggable constituents table
│       │   ├── PriceChart/            # Zoomable area chart — ETF or individual stock
│       │   ├── TopHoldingsChart/      # Bar chart — top N by holding size
│       │   └── Layout/                # Sidebar + Dashboard + ETF header banner
│       ├── types/etf.ts               # Shared TypeScript interfaces
│       └── utils/formatters.ts        # Currency, percent, date formatters
│
└── db/
    └── init/
        ├── 01_schema.sql              # Schema creation (idempotent)
        └── 02_seed.sql                # Unpivots prices.csv wide→long, seeds once
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/health` | Service + DB health check |
| `POST` | `/api/v1/etf/upload` | Upload ETF CSV; returns parsed summary |
| `GET` | `/api/v1/etf/session` | All ETFs uploaded in this session |
| `GET` | `/api/v1/etf/{id}` | ETF summary with constituents + latest prices |
| `GET` | `/api/v1/etf/{id}/price-history` | Reconstructed ETF price time series |
| `GET` | `/api/v1/etf/{id}/top-holdings` | Top N holdings by holding size (`?limit=5`) |
| `GET` | `/api/v1/etf/stock/{name}/price-history` | Price history for a single stock |
| `DELETE` | `/api/v1/etf/{id}` | Delete an ETF from the current session |

Full interactive docs at `https://etf-price-monitor.onrender.com/api/docs`.

---

## ETF Price Calculation

The reconstructed ETF price at time `t` is:

ETF_price(t) = Σ weight_i × price_i(t)

Computed in a single SQL aggregation — no Python-side aggregation:

```sql
SELECT p.date, SUM(ec.weight * p.close_price) AS etf_price
FROM etf_constituents ec
JOIN prices p ON p.stock_name = ec.stock_name
WHERE ec.etf_id = :etf_id
GROUP BY p.date
ORDER BY p.date ASC
```

---

## Assumptions

1. **Weights are static over time** — weight columns in ETF CSVs apply uniformly across all historical dates.
2. **Prices CSV is authoritative** — uploading an ETF with an unknown stock name is rejected with a `422` error and a clear message.
3. **Weight validation** — each weight must be `> 0` and `≤ 1`. Weights don't need to sum exactly to 1.0.
4. **No authentication** — users are identified by an anonymous `session_id` cookie. Adding JWT auth requires changing only the `get_or_create_session` dependency.
<!-- 5. **Proportional rebalancing on delete** — when a constituent is deleted, remaining weights are rebalanced proportionally. -->

---

## Future Improvements

### Planned Features
- **Proportional weight rebalancing on delete** — when a constituent is deleted from an ETF, remaining weights are automatically rebalanced proportionally so they continue to sum to 1.0
- **Hide row** — toggle individual row visibility in the holdings table without removing the constituent
- **Pin row to top** — pin a specific constituent to always appear at the top of the table regardless of sort order
- **Inline editing** — edit constituent weights directly in the table; recalculates price chart and top holdings in real time
- **Multi-row selection** — select multiple constituents and view their combined or overlaid price histories on the chart
- **Authentication** — replace anonymous session cookies with JWT-based auth; `session_id` in the DB schema becomes a `user_id` FK — the only required code change is swapping the `get_or_create_session` dependency in `routers/etf.py`

### Infrastructure
- **TimescaleDB in production** — migrate from Render Postgres to Timescale Cloud for hypertable chunk exclusion at scale; no application code changes required
- **PgBouncer connection pooling** — add a connection pooler between backend instances and the DB for horizontal scaling
- **Rate limiting** — add per-IP rate limiting on the upload endpoint using `slowapi` to prevent abuse
- **Security headers** — add `X-Content-Type-Options`, `X-Frame-Options`, and `Content-Security-Policy` response headers
- **Kubernetes deployment** — migrate from Docker Compose to K8s manifests with HPA for auto-scaling under load
- **Market data ingestion** — replace the seeded CSV with a real-time market data feed (Kafka consumer writing to the prices hypertable)

---

## Design Decisions for Scale

|  Concern | Current | Path to scale |
|----------|---------|---------------|
| DB reads | Single Postgres instance | Read replicas behind PgBouncer connection pooler |
| Price history queries | Standard Postgres index scan | TimescaleDB hypertable + chunk exclusion at scale |
| Horizontal scaling | Single backend pod | Stateless FastAPI — scale with K8s HPA |
| Session state | DB-backed cookie | Swap `get_or_create_session` for JWT — no other changes |
| Price data source | Seeded CSV | Replace seed with market data ingestion job (Kafka consumer) |
| Logging | Structured JSON to stdout | Ship to Datadog / CloudWatch via log driver — zero code changes |
| Price history queries | Standard Postgres index scan | Migrate to Timescale Cloud for hypertable chunk exclusion at scale |

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

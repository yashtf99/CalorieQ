# CalorieQ — Backend

**Stack:** FastAPI · SQLAlchemy 2 · Pydantic v2 · SQLite (dev) / MySQL 8+ (prod) · pytz  
**Tests:** 146 passing · **Docs:** `docs/`

---

## How to Run

**Prerequisites:** Python 3.13, virtual environment set up.

```bash
cd backend
py -3.13 -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
pip install -r requirements-dev.txt   # for tests
```

Copy the env file and fill in secrets:

```bash
cp .env.example .env
# Set SECRET_KEY and AWS_BEARER_TOKEN_BEDROCK
```

Start the dev server:

```bash
uvicorn app.main:app --reload
```

API available at `http://localhost:8000`. Interactive docs at `/docs`.

Run tests:

```bash
pytest
```

---

## Architecture

```
HTTP request
    │
    ▼
app/api/v1/*.py      ← input validation (Pydantic schemas + params.py)
    │
    ▼
app/services/*.py    ← all business logic; routers never touch the DB directly
    │
    ├── app/models/*.py      ← SQLAlchemy ORM + CheckConstraints
    └── app/orm/session.py   ← DatabasePool singleton, get_db() dependency
```

No service imports another service. No model imports a service.

---

## Directory Layout

```
backend/
├── app/
│   ├── main.py              # FastAPI app, CORS, exception handlers, router mount
│   ├── api/
│   │   ├── deps.py          # get_current_user (HTTPBearer → JWT decode → User row)
│   │   └── v1/
│   │       ├── router.py    # Aggregates all sub-routers under /api/v1
│   │       ├── auth.py
│   │       ├── users.py
│   │       ├── goals.py
│   │       ├── food_items.py
│   │       ├── meals.py
│   │       └── reports.py
│   ├── core/
│   │   ├── constraints.py   # ★ Single source of truth for all numeric bounds
│   │   ├── exceptions.py    # HTTPException subclasses (NotFoundError, ForbiddenError, …)
│   │   └── security.py      # bcrypt hashing (SHA-256 pre-hash), JWT create/decode, refresh token utils
│   ├── models/              # SQLAlchemy ORM — one file per table
│   ├── orm/
│   │   ├── base.py          # DeclarativeBase
│   │   └── session.py       # DatabasePool singleton, get_db() FastAPI dependency
│   ├── schemas/             # Pydantic v2 request/response shapes
│   │   ├── params.py        # Query-param dependency classes (MealListParams, ReportRangeParams, …)
│   │   └── common.py        # PaginatedResponse[T], make_paginated()
│   └── services/            # Business logic — one file per domain
├── config.py                # Pydantic BaseSettings — DATABASE_URL, SECRET_KEY, AWS config
├── db/
│   ├── schema.sql           # Reference DDL (SQLite)
│   ├── create_db.py         # Schema creation script (python db/create_db.py [--drop])
│   └── calorieq.db          # SQLite dev DB (gitignored)
├── data/                    # Raw + processed food data for ingestion
├── ingestion/               # Adapter + Strategy classes used by ingest.py
├── ingest.py                # One-time food data seed script
├── tests/
│   ├── conftest.py          # In-memory SQLite fixtures, get_db override, token_headers fixture
│   ├── test_auth.py
│   ├── test_users.py
│   ├── test_goals.py
│   ├── test_meals.py
│   ├── test_meal_timezones.py
│   ├── test_reports.py
│   └── test_bugs.py         # Regression tests for past bug fixes
├── requirements.txt
├── requirements-dev.txt
└── pytest.ini
```

---

## Key Design Decisions

### `app/core/constraints.py` — numeric bounds SSoT

All input limits (quantity, calories, macros, weight, etc.) live here as plain constants. Pydantic schemas import them into `Field(gt=..., lt=...)` for HTTP-layer validation; SQLAlchemy models import them into `CheckConstraint(...)` for DB-level defense. Change a value once — both layers update automatically.

### Auth — two-token scheme

| Token | Type | Lifetime | Storage |
|---|---|---|---|
| Access | JWT (HS256) | 24 h | Client only |
| Refresh | Opaque random | 30 days | DB as SHA-256 hash |

- Refresh tokens are rotated on every `/auth/refresh` call — a reused token signals theft and forces re-login.
- Passwords are SHA-256 pre-hashed before bcrypt to avoid bcrypt's 72-byte truncation vulnerability.
- JWT decode uses an explicit algorithm allowlist (`HS256` only) — `alg: none` attacks are rejected.

### Macro denormalization in `user_meal_logs`

Key macros (calories, protein, carbs, fat, fibre, sodium) are scaled to the logged quantity and stored directly on the meal log row at write time. Report queries are fast and past entries are unaffected by later edits to `food_items`. Micronutrient reports JOIN back to `food_items` on demand (via `food_item_id`); free-form entries without a linked item are excluded from micro reports.

### Versioned goals

Creating a new goal closes the previous one (`active_to` is set to now). Only one goal has `active_to = NULL` at a time. History is preserved for goal-vs-actual charts.

### Timezone handling

`logged_at` is always stored as naive UTC. Date-filtered endpoints accept a `tz` param (IANA string, e.g. `Asia/Kolkata`); day boundaries are resolved in the user's local timezone via pytz so "today" means the correct local day.

---

## API Overview

Base URL: `/api/v1`. Full spec in `docs/api-spec.md`.

| # | Method | Path | Notes |
|---|---|---|---|
| 1–4 | POST | `/auth/*` | register, login, refresh, logout |
| 5–8 | GET/PATCH | `/users/me`, `/users/me/profile` | |
| 9–11 | POST/GET | `/goals`, `/goals/active`, `/goals/history` | versioned |
| 12–16 | GET/POST/PATCH/DELETE | `/food_items` | search + user_custom CRUD |
| 17–21 | POST/GET/PATCH/DELETE | `/meals`, `/meals/history`, `/meals/{id}` | |
| 22–24 | GET | `/reports/daily_summary`, `/reports/weekly`, `/reports/micros` | |

---

## Database Setup & Food Data Ingestion

Run once to set up the DB and seed food data (~8,800 items from INDB and USDA SR Legacy).

### 1. Create the schema

```bash
python db/create_db.py
```

Creates `db/calorieq.db` with all tables. Re-run is safe (`CREATE IF NOT EXISTS`). To wipe and recreate:

```bash
python db/create_db.py --drop
```

### 2. Process raw INDB Excel files (one-time only)

```bash
python data/process_raw_data.py
```

Output lands in `data/INDB-processed/`. USDA data ships as CSV — no processing needed.

### 3. Ingest food data

```bash
python ingest.py
```

Idempotent — re-running clears and reloads only seeded rows. User-created entries (`source = 'user_custom'`) are never touched.

| Source | Items | Coverage |
|---|---|---|
| INDB | 1,014 | Indian recipes — macros + 30 micros per 100 g |
| USDA SR Legacy | 7,793 | Raw ingredients — macros + 37 micros per 100 g + portion weights |

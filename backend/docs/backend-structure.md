# CalorieQ — Backend Structure

**Stack:** FastAPI · Pydantic v2 · SQLAlchemy 2 (ORM) · SQLite (dev) / MySQL 8+ (prod) · AWS Bedrock · pytz

Run: `uvicorn app.main:app --reload` from the `backend/` directory.

---

## Directory layout

```
backend/
├── app/
│   ├── main.py              # FastAPI app, CORS, exception handlers, router mount
│   ├── api/
│   │   ├── deps.py          # get_current_user (HTTPBearer → JWT decode → User row)
│   │   └── v1/
│   │       ├── router.py    # Aggregates all sub-routers under /api/v1
│   │       ├── auth.py      # /auth/*
│   │       ├── users.py     # /users/me, /users/me/profile
│   │       ├── goals.py     # /goals
│   │       ├── food_items.py# /food_items
│   │       ├── meals.py     # /meals
│   │       └── reports.py   # /reports/*
│   ├── core/
│   │   ├── constraints.py   # ★ Single source of truth for all numeric bounds
│   │   ├── exceptions.py    # HTTPException subclasses (NotFoundError, ForbiddenError, …)
│   │   └── security.py      # bcrypt hashing (SHA-256 pre-hash), JWT create/decode, refresh token utils
│   ├── models/              # SQLAlchemy ORM — one file per table
│   │   ├── user.py
│   │   ├── refresh_token.py
│   │   ├── user_profile.py
│   │   ├── goal.py
│   │   ├── food_item.py
│   │   ├── food_portion.py
│   │   ├── meal_log.py
│   │   └── weight_log.py
│   ├── orm/
│   │   ├── base.py          # DeclarativeBase
│   │   └── session.py       # DatabasePool singleton, get_db() FastAPI dependency
│   ├── schemas/             # Pydantic v2 — request bodies and response shapes
│   │   ├── auth.py          # RegisterRequest, LoginRequest, TokenResponse, …
│   │   ├── user.py          # UserOut, UserUpdateIn, UserProfileIn, UserProfileOut
│   │   ├── goal.py          # GoalIn, GoalOut
│   │   ├── food_item.py     # FoodItemSearchOut, FoodItemDetailOut, CustomFoodItemIn
│   │   ├── meal_log.py      # MealLogIn, MealLogPatchIn, MealLogOut
│   │   ├── report.py        # DailySummaryOut, WeeklyReportOut, MicrosReportOut
│   │   ├── params.py        # Query-param dependency classes (MealListParams, ReportRangeParams, …)
│   │   └── common.py        # PaginatedResponse[T], make_paginated()
│   └── services/            # All business logic — routers call services, never the DB directly
│       ├── auth_service.py
│       ├── user_service.py
│       ├── goal_service.py
│       ├── food_service.py
│       ├── meal_log_service.py
│       └── report_service.py
├── config.py                # Pydantic BaseSettings — DATABASE_URL, SECRET_KEY, AWS config
├── db/
│   ├── schema.sql           # Reference DDL (SQLite)
│   ├── create_db.py         # Schema creation script (python db/create_db.py [--drop])
│   └── calorieq.db          # SQLite dev DB (gitignored)
├── ingestion/               # One-time INDB + USDA food data loader
├── ingest.py                # Entry point: python ingest.py
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
├── requirements-dev.txt     # pytest
└── pytest.ini
```

---

## `app/core/constraints.py` — single source of truth

All numeric bounds (min/max values for quantities, calories, macros, etc.) live here as plain constants.

- **Pydantic schemas** import them into `Field(gt=..., lt=...)` — rejects bad input at the HTTP layer.
- **SQLAlchemy models** import them into `CheckConstraint(f"col > {CONST}")` — DB-level defense in depth.

Change a value once, both layers update automatically.

---

## `app/core/security.py`

- **Password hashing:** `bcrypt` with SHA-256 pre-hash (avoids bcrypt's 72-byte truncation vulnerability).
- **Access tokens:** short-lived JWT (HS256, 24 h), carries `sub` (user_id) and `type: "access"`.
- **Refresh tokens:** opaque `secrets.token_urlsafe(32)`, stored as SHA-256 hash in `refresh_tokens` table. Rotated on every `/auth/refresh` call.

---

## `app/schemas/params.py`

Query-parameter validation that can't live in Pydantic body models (FastAPI `Depends`-based classes):

| Class | Used by | Validates |
|---|---|---|
| `MealListParams` | `GET /meals` | date/start/end format, mutual exclusion, tz validity |
| `ReportRangeParams` | `GET /reports/weekly`, `GET /reports/micros` | week_of/start/end format, tz validity |
| `DailySummaryParams` | `GET /reports/daily_summary` | date format, tz validity |

Input format validation (date strings, timezone names) lives here.
Business rule validation (range caps, logic) stays in the service.

---

## Services — responsibility split

| Service | Owns |
|---|---|
| `auth_service` | register (email uniqueness via IntegrityError), login, token issuance/rotation/revocation |
| `user_service` | update display name, get/update profile, weight log creation on profile PATCH |
| `goal_service` | create goal (closes previous), get active, paginated history |
| `food_service` | search (ILIKE), detail + portions, create/update/delete user_custom |
| `meal_log_service` | create (scales macros from food item per-100g), list (tz-aware), update, delete |
| `report_service` | daily summary, weekly macro+goal report, micros; `resolve_range()` + week-snapping |

---

## Dependency flow

```
HTTP request
    │
    ▼
app/api/v1/*.py          ← input validation via schemas/ and params/
    │
    ▼
app/services/*.py        ← business logic, DB reads/writes
    │
    ├── app/models/*.py  ← ORM column definitions + CheckConstraints
    └── app/orm/session.py
```

No service imports another service. No model imports a service.

---

## Not yet implemented (planned)

- `POST /weight_logs`, `GET /weight_logs` — standalone weight log CRUD (model exists, used internally by profile PATCH)
- `POST /ai/extract_image` — Bedrock vision → nutrition pre-fill
- `POST /ai/import_pdf` — PDF diary → bulk meal import
- `POST /chat/sessions/{id}/messages` — LangGraph conversational agent
- `DELETE /users/me` — account deletion

# CalorieQ — Backend Directory Structure

**Stack:** FastAPI · Pydantic v2 · SQLAlchemy · MySQL 8+ · AWS Bedrock · LangGraph

---

## Top-level layout

```
backend/
├── app/                   # All application source code
│   ├── main.py
│   ├── config.py
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── chat/
├── alembic.ini
├── requirements.txt
├── .env
└── .env.example
```

---

## `app/main.py`

FastAPI app instantiation, middleware registration (CORS, request-id), and router mounting.
This is the single entry point — `uvicorn app.main:app`.

## `app/config.py`

Pydantic `BaseSettings` class that reads all env vars (`.env` file in dev, real env in prod).
Holds DB URL, JWT secret, AWS region, Bedrock model ID.
Exported as a singleton `settings` so every module imports from one place.

---

## `app/api/`

**Route handlers only — no business logic here.**
Each file maps 1-to-1 with a feature domain. Handlers call into `services/`, validate with `schemas/`, and return shaped responses.

```
app/api/
├── deps.py          # Shared FastAPI dependencies: get_db (DB session), get_current_user (JWT decode)
└── v1/
    ├── router.py    # Aggregates all sub-routers under /api/v1
    ├── auth.py      # POST /auth/register, POST /auth/login, POST /auth/refresh
    ├── users.py     # GET/PATCH /users/me, GET/PATCH /users/me/profile
    ├── goals.py     # POST /goals, GET /goals/active, GET /goals/history
    ├── food_items.py      # GET /foods (search), POST /foods (user_custom), GET /foods/{id}
    ├── meal_logs.py       # POST /logs, GET /logs (date-range + meal_type filter), PATCH/DELETE /logs/{id}
    ├── weight_logs.py     # POST /weight, GET /weight (history)
    ├── reports.py         # GET /reports/weekly-calories, /reports/macros, /reports/micros, /reports/goal-vs-actual
    ├── chat.py            # POST /chat/sessions, GET /chat/sessions, POST /chat/sessions/{id}/messages (streaming)
    ├── ai_extraction.py   # POST /ai/extract-image → async job; GET /ai/jobs/{job_id}
    └── pdf_import.py      # POST /ai/import-pdf → async job; GET /ai/jobs/{job_id}
```

**Why versioned (`v1/`)?** All AI features are async with polling endpoints — the contract will evolve. Versioning lets us break the AI surface without touching stable meal-log endpoints.

---

## `app/core/`

Cross-cutting concerns shared by every layer.

```
app/core/
├── security.py     # Password hashing (bcrypt), JWT create/decode, token models
├── exceptions.py   # Custom HTTPException subclasses (NotFound, Forbidden, Conflict, UnprocessableEntity)
└── logging.py      # Structured JSON logger configuration; request-id propagation
```

---

## `app/orm/`

SQLAlchemy ORM infrastructure — engine, session factory, declarative base, and Alembic migrations.
Named `orm/` to distinguish it from `backend/db/` which holds the ops scripts and the SQLite DB file.

```
app/orm/
├── session.py     # create_engine(), SessionLocal, get_db() FastAPI dependency
├── base.py        # DeclarativeBase; imports all models so Alembic autogenerates correctly
└── migrations/    # Alembic managed
    ├── env.py
    ├── script.py.mako
    └── versions/  # One file per migration — never edited after commit
```

---

## `app/models/`

SQLAlchemy ORM table definitions. One file per entity from `entities.md`.

```
app/models/
├── user.py          # users table
├── user_profile.py  # user_profiles table
├── goal.py          # goals table (versioned rows)
├── food_item.py     # food_items table (INDB + USDA + user_custom)
├── food_portion.py  # food_portions table
├── meal_log.py      # user_meal_logs table (denormalized macros)
├── weight_log.py    # weight_logs table
├── chat_session.py  # chat_sessions table
└── chat_message.py  # chat_messages table (user_query + chat_response pairs)
```

Models hold **no business logic** — only column definitions, relationships, and `__tablename__`.
Nutrient values on `food_items` are per-100g; scaling to `quantity_g` is done in the service layer when writing `user_meal_logs`.

---

## `app/schemas/`

Pydantic v2 models for request validation and response serialisation. Kept separate from ORM models so the API surface and DB schema can evolve independently.

```
app/schemas/
├── auth.py        # RegisterRequest, LoginRequest, TokenResponse
├── user.py        # UserOut, UserProfileIn, UserProfileOut
├── goal.py        # GoalIn, GoalOut
├── food_item.py   # FoodItemOut, FoodItemSearch, CustomFoodItemIn
├── meal_log.py    # MealLogIn, MealLogOut, MealLogListParams
├── weight_log.py  # WeightLogIn, WeightLogOut
├── reports.py     # WeeklyCalorieReport, MacroBreakdown, MicroSummary, GoalVsActual
├── chat.py        # ChatSessionOut, ChatMessageIn, ChatMessageOut, StreamChunk
└── ai.py          # ExtractionJobOut, ImportJobOut, JobStatus (pending/done/failed)
```

**Pattern used:** `XIn` = inbound request body; `XOut` = outbound response; list endpoints return `list[XOut]` wrapped in a common paginated envelope.

---

## `app/services/`

All business logic lives here. Routers call services; services call models + DB session.
Each service is a plain Python module (no class hierarchies unless state is needed).

```
app/services/
├── auth_service.py        # register, login, issue/verify JWT
├── user_service.py        # read/update user, read/update profile
├── goal_service.py        # create goal (inserts new row, closes previous), get active goal
├── food_service.py        # food search (name FTS + filter by source), create custom food
├── meal_log_service.py    # create log (scales nutrients), list with filters, update, delete
├── weight_log_service.py  # add weight entry, get history
├── report_service.py      # all aggregation queries for the reports endpoints
└── ai/
    ├── bedrock_client.py      # Thin wrapper around boto3 bedrock-runtime; exposes invoke_model() uses global.amazon.nova-2-lite-v1:0
    ├── extraction_service.py  # Receives image bytes → calls Bedrock vision model → parses structured nutrition JSON → returns async job result
    └── pdf_import_service.py  # Receives PDF bytes → extracts text → calls Bedrock text model → parses tabular meal entries → bulk-inserts to meal_logs
```

**Why async jobs for AI?** Per the non-functional requirements: "Keep AI operations async — return an immediate 'processing' response and let the client poll." LLM/vision calls can exceed 10 s; blocking a request thread for that long breaks uvicorn workers under load.

---

## `app/chat/`

Self-contained LangGraph conversational agent. The `chat.py` API router calls into this module; nothing else in the codebase touches LangGraph directly.

```
app/chat/
├── state.py     # CalorieQState TypedDict — holds messages[], user_id, session_id, tool_results
├── graph.py     # StateGraph definition: wires nodes together, compiles the runnable graph
├── nodes.py     # Graph node functions: intent_router, tool_executor, responder, guard_rails
├── tools.py     # LangChain @tool definitions the agent can call:
│                #   log_meal_tool, get_daily_summary_tool, check_goals_tool,
│                #   search_food_tool, get_weekly_report_tool
└── memory.py    # LangGraph checkpointer wiring — uses chat_sessions/chat_messages
│                # tables (or SqliteSaver in dev) to persist multi-turn context per session
```

**Why LangGraph?** The chat feature must support multi-step agentic flows (e.g., "log my lunch" → ask clarifying questions → search food DB → confirm → write meal log). LangGraph's explicit state machine makes those transitions testable and auditable vs. a raw while-loop agent.

**Tool → service boundary:** Each tool in `tools.py` calls the corresponding function in `app/services/` — the agent has no direct DB access. This keeps the service layer the single source of truth for writes.

---

## Dependency flow (read top-down, no upward imports)

```
api/v1/*.py
    └── services/*.py
            ├── models/*.py  (ORM)
            ├── db/session.py
            └── services/ai/  (Bedrock calls)

api/v1/chat.py
    └── chat/graph.py
            └── chat/tools.py
                    └── services/*.py  (same service layer)
```

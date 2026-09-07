# CalorieQ
The Personal Calorie Tracker is a full-stack application designed to help users monitor, manage,
and understand their daily nutritional intake. Users can log meals across breakfast, lunch, and
dinner, set personalized health goals, and visualize macro and micronutrient trends over time.

| Layer | Stack |
|---|---|
| **Backend** | Python 3.13 · FastAPI · SQLAlchemy 2 · Pydantic v2 · LangGraph |
| **Database** | SQLite (dev) / MySQL 8+ (prod) |
| **Frontend** | React 19 · TypeScript · Vite 8 · Tailwind CSS v4 · shadcn/ui · TanStack Query v5 |
| **AI** | AWS Bedrock (Claude) — image extraction + conversational chat agent |

## First-Time Setup

> Run these steps once after cloning the repo. After that, use the start scripts below.

### 1. Backend — Python environment & dependencies

Requires **Python 3.13**.

```bash
cd backend
py -3.13 -m venv .venv
source .venv/Scripts/activate       # Git Bash on Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt  # optional — only needed to run tests
```

### 2. API keys

```bash
cp backend/.env.example backend/.env
```

Open `backend/.env` and fill in:

| Variable | What it is |
|---|---|
| `SECRET_KEY` | Any long random string — used to sign JWTs |
| `AWS_BEARER_TOKEN_BEDROCK` | AWS Bedrock bearer token — used by the AI/chat features |

> Non-secret config (DB URL, AWS region, model IDs) lives in `backend/config.py` — no edits needed for local dev.

### 3. Create the database

```bash
cd backend
source .venv/Scripts/activate       # if not already active
python db/create_db.py
```

Creates `backend/db/calorieq.db`. Re-running is safe. To wipe and recreate:

```bash
python db/create_db.py --drop
```

### 4. Ingest food data (~8,800 items — run once)

```bash
# Still inside backend/ with venv active

# Process raw INDB Excel files → CSV (one-time only)
python data/process_raw_data.py

# Seed the database (idempotent — safe to re-run)
python ingest.py
```

| Source | Items | Notes |
|---|---|---|
| INDB | 1,014 | Indian recipes — macros + 30 micros |
| USDA SR Legacy | 7,793 | Raw ingredients — macros + 37 micros |

### 5. Frontend — Node dependencies

Requires **Node.js ≥ 20.19**.

```bash
cd frontend
npm install
cp .env.example .env   # default already points to http://localhost:8000/api/v1
```

---

## Dev Setup

### Start servers

Open two terminals and run one command each:

```bash
# Terminal 1 — backend (http://localhost:8000)
cd backend && bash start.sh

# Terminal 2 — frontend (http://localhost:5173)
cd frontend && bash start.sh
```

**What the scripts do:**
- **Backend** (`backend/start.sh`):
  - Activates the Python virtual environment (`.venv`)
  - Starts Uvicorn server with auto-reload on file changes
  - Logs to `backend/logs/backend.log` with timestamps
  
- **Frontend** (`frontend/start.sh`):
  - Starts Vite dev server (HMR enabled for live code updates)
  - Logs to `frontend/logs/frontend.log` with timestamps
  - Strips ANSI color codes for clean log files

**Monitor logs live:**
```bash
tail -f backend/logs/backend.log
tail -f frontend/logs/frontend.log
```

**Troubleshooting:**
- If `start.sh` fails: ensure you're in the correct directory (`backend/` or `frontend/`)
- If permission denied: run `chmod +x start.sh` in that directory
- If port already in use: kill processes below, then retry

### Kill processes

When you need to stop the servers (or if they're stuck):

**Git Bash / WSL:**
```bash
# Kill all Python processes (backend)
taskkill //F //IM python.exe

# Kill all Node processes (frontend)
taskkill //F //IM node.exe

# Or kill both at once
taskkill //F //IM uvicorn.exe; taskkill //F //IM node.exe; taskkill //F //IM python.exe
```

**PowerShell:**
```powershell
# Kill by process name
taskkill /F /IM python.exe
taskkill /F /IM node.exe

# Or kill both
taskkill /F /IM uvicorn.exe; taskkill /F /IM node.exe; taskkill /F /IM python.exe
```

**Kill by port (find and kill a specific process):**
```powershell
# Find what's using port 8000 (backend)
netstat -ano | findstr :8000
# Output: TCP  127.0.0.1:8000  0.0.0.0:0  LISTENING  12345
# Kill by PID
taskkill /F /PID 12345

# Find what's using port 5173 (frontend)
netstat -ano | findstr :5173
```

**Verify processes are stopped:**
```bash
# Check if ports are free
netstat -ano | findstr ":8000\|:5173"
# Should return nothing if both are stopped
```

---

## Requirements Completion

### Core Requirements

| Status | Requirement |
|---|---|
| ✅ | **Goal Setting** — Set and manage personal health goals (daily calorie target, protein/carb/fat targets, weight goal) through the web app |
| ✅ | **Meal Entry** — Create food entries grouped by meal type (Breakfast, Lunch, Dinner, Snacks) with food item name, quantity, calories, macros, and micros |
| ✅ | **Time-Range Listing** — List all food entries in a specified time range, filterable by date and meal type |
| ✅ | **Nutrition Reports & Graphs** — Weekly calorie trend, macronutrient breakdown by day/week, micronutrient summary, and goal vs. actual comparison charts |
| ✅ | **AI-Powered Calorie Extraction** — Upload a photo (nutrition label or food plate) to automatically extract and pre-fill nutritional information using AI image analysis |

### Bonus Features

| Status | Requirement |
|---|---|
| ✅ | **Conversational Chat Interface** — LLM-powered chat that lets users log meals, check goals, ask nutritional questions, and get weekly summaries through natural language |
| ✅ | **Multi-User Support** — Multiple independent users can sign up, log in, and maintain their own private data |
| ⬜ | **Bulk Import via PDF** — Upload a food diary or nutrition history exported as PDF (tabular format) and automatically parse and import entries |

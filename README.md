# CalorieQ
The Personal Calorie Tracker is a full-stack application designed to help users monitor, manage,
and understand their daily nutritional intake. Users can log meals across breakfast, lunch, and
dinner, set personalized health goals, and visualize macro and micronutrient trends over time.

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

## Functional Requirements (directly from Stakeholders)

- Multi-User Support: Support multiple independent users who can sign up, log in, and
maintain their own private data.
- Goal Setting: Ability to set and manage personal health goals (e.g., daily calorie target,
protein/carb/fat targets, weight goal) through the web app.
- Meal Entry: Ability to create food entries grouped by meal type (Breakfast, Lunch, Dinner,
Snacks) with fields for food item name, quantity, and nutritional values (calories, macros,
micros).
- Time-Range Listing: List all food entries in a specified time range through the web app,
filterable by date and meal type.
- Nutrition Reports & Graphs: Ability to display visual reports including: weekly calorie intake
trend, macronutrient breakdown (protein, carbs, fat) by day/week, micronutrient summary
(vitamins, minerals), and goal vs. actual comparison charts.
- AI-Powered Calorie Extraction: Ability to upload a photo (product nutrition label or a plate
of food) and automatically extract and pre-fill calorie and nutritional information using AI image
analysis.
- Conversational Chat Interface: Build a chat interface powered by an LLM that allows users
to perform all app actions through natural language — logging meals, checking goals, asking
nutritional questions, and getting weekly summaries — without touching traditional UI controls
- Bulk Import via PDF: Support upload of a food diary or nutrition history exported as a PDF
(tabular format) and automatically parse and import the entries.


## Non-Functional Requirements

- Strict per-user data isolation — nutrition/health data is sensitive.
- Basic validation on nutrition values (no negative calories, sensible upper bounds) — matters since AI extraction can be noisy.
- Core meal logging and goal-setting must work even if the AI subsystem (LLM, vision model) is down — graceful degradation, not hard dependency.
- Keep AI operations async — return an immediate "processing" response and let the client poll for results, rather than blocking on a 5+ second LLM call.
- Idempotency for AI-triggered writes (re-uploading the same photo for same period shouldn't create duplicates).
- [Future] Hard per-user rate limits on AI-triggered operations (image extraction, chat) to prevent runaway costs from a single user.

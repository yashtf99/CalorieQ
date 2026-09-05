# Data Ingestion

Seeds the SQLite database with ~8,800 food items from two sources:

| Source | Items | Coverage |
|---|---|---|
| INDB | 1,014 | Indian recipes — macros + 30 micros per 100 g |
| USDA SR Legacy | 7,793 | Raw ingredients — macros + 37 micros per 100 g + portion weights |

---

## Prerequisites

**Python 3.13** and the virtual environment set up:

```bash
cd backend
py -3.13 -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

**Secrets** — create `backend/.env` from the example and fill in values:

```bash
cp .env.example .env
# then open .env and set SECRET_KEY and AWS_BEARER_TOKEN_BEDROCK
```

---

## Steps

All commands are run from the `backend/` directory.

### 1. Process raw Excel files → CSV

Only needed once. Converts INDB source `.xlsx` files into CSVs used by the ingestion script.

```bash
python data/process_raw_data.py
```

Output lands in `data/INDB-processed/`. USDA data ships as CSV already — no processing needed.

### 2. Create the database schema

Creates `db/calorieq.db` with all 9 tables.

```bash
python db/create_db.py
```

Safe to re-run (uses `CREATE IF NOT EXISTS`). To wipe and recreate from scratch:

```bash
python db/create_db.py --drop
```

### 3. Ingest food data

```bash
python ingest.py
```

Expected output:

```
[INDB] Starting ...
  Cleared 0 existing 'indb' rows
  [indb] 1014 food items inserted
[INDB] Committed.

[USDA] Starting ...
  Cleared 0 existing 'usda' rows
  [usda] 7793 food items, 14449 portions inserted
[USDA] Committed.

All datasets ingested successfully.
```

Ingestion is **idempotent** — re-running clears and reloads only the seeded rows. User-created food entries (`source = 'user_custom'`) are never touched.

---

## File layout

```
backend/
├── data/
│   ├── INDB-raw-data/        # Source Excel files (committed)
│   ├── INDB-processed/       # Generated CSVs — recreated by process_raw_data.py
│   ├── USDA-raw-data/        # Source CSVs (committed)
│   └── process_raw_data.py   # Step 1 script
├── db/
│   ├── schema.sql            # Reference DDL
│   ├── create_db.py          # Step 2 script
│   └── calorieq.db           # SQLite DB file (gitignored)
├── ingestion/                # Adapter + Strategy classes used by ingest.py
└── ingest.py                 # Step 3 script
```

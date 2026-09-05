-- CalorieQ — SQLite Reference DDL
-- Dependency order: users → profiles/goals → food_items → portions/logs → chat
--
-- SQLite differences from MySQL:
--   • No ENGINE / CHARSET clauses
--   • ENUM replaced by TEXT + CHECK constraint
--   • No ON UPDATE CURRENT_TIMESTAMP — updated_at is set by the application layer
--   • BOOLEAN stored as INTEGER (0/1)
--   • DECIMAL/CHAR/VARCHAR are all TEXT affinity — stored exactly as given

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS users (
  id            TEXT     NOT NULL,
  email         TEXT     NOT NULL,
  password_hash TEXT     NOT NULL,
  display_name  TEXT,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE (email)
);


CREATE TABLE IF NOT EXISTS user_profiles (
  user_id        TEXT     NOT NULL,
  dob            DATE,
  gender         TEXT,
  height_cm      REAL,
  activity_level TEXT,
  updated_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id),
  FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS goals (
  id               TEXT     NOT NULL,
  user_id          TEXT     NOT NULL,
  goal_type        TEXT     NOT NULL CHECK (goal_type IN ('lose', 'maintain', 'gain')),
  daily_calories   REAL,
  protein_g        REAL,
  carbs_g          REAL,
  fat_g            REAL,
  fibre_g          REAL,
  weight_target_kg REAL,
  active_from      DATETIME NOT NULL,
  active_to        DATETIME,
  created_at       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_goals_user_active ON goals (user_id, active_to);


CREATE TABLE IF NOT EXISTS food_items (
  id             TEXT     NOT NULL,
  source         TEXT     NOT NULL,
  external_id    TEXT,
  name           TEXT     NOT NULL,
  category       TEXT,
  energy_kcal    REAL,
  energy_kj      REAL,
  protein_g      REAL,
  carb_g         REAL,
  fat_g          REAL,
  freesugar_g    REAL,
  fibre_g        REAL,
  sfa_g          REAL,
  mufa_g         REAL,
  pufa_g         REAL,
  cholesterol_mg REAL,
  calcium_mg     REAL,
  phosphorus_mg  REAL,
  magnesium_mg   REAL,
  sodium_mg      REAL,
  potassium_mg   REAL,
  iron_mg        REAL,
  copper_mg      REAL,
  selenium_ug    REAL,
  chromium_mg    REAL,
  manganese_mg   REAL,
  molybdenum_mg  REAL,
  zinc_mg        REAL,
  vita_ug        REAL,
  vite_mg        REAL,
  vitd2_ug       REAL,
  vitd3_ug       REAL,
  vitk1_ug       REAL,
  vitk2_ug       REAL,
  folate_ug      REAL,
  vitb1_mg       REAL,
  vitb2_mg       REAL,
  vitb3_mg       REAL,
  vitb5_mg       REAL,
  vitb6_mg       REAL,
  vitb7_ug       REAL,
  vitb9_ug       REAL,
  vitc_mg        REAL,
  carotenoids_ug REAL,
  is_verified    INTEGER  NOT NULL DEFAULT 1,
  created_by     TEXT,
  created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_food_source ON food_items (source);
CREATE INDEX IF NOT EXISTS idx_food_name   ON food_items (name);


CREATE TABLE IF NOT EXISTS food_portions (
  id           TEXT NOT NULL,
  food_item_id TEXT NOT NULL,
  description  TEXT NOT NULL,
  gram_weight  REAL NOT NULL,
  created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  FOREIGN KEY (food_item_id) REFERENCES food_items (id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS user_meal_logs (
  id                 TEXT     NOT NULL,
  user_id            TEXT     NOT NULL,
  food_item_id       TEXT,
  logged_at          DATETIME NOT NULL,
  meal_type          TEXT     NOT NULL,
  food_name_snapshot TEXT     NOT NULL,
  quantity_g         REAL     NOT NULL,
  energy_kcal        REAL     NOT NULL,
  protein_g          REAL     NOT NULL,
  carb_g             REAL     NOT NULL,
  fat_g              REAL     NOT NULL,
  fibre_g            REAL,
  sodium_mg          REAL,
  source             TEXT     NOT NULL,
  notes              TEXT,
  created_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  FOREIGN KEY (user_id)      REFERENCES users      (id) ON DELETE CASCADE,
  FOREIGN KEY (food_item_id) REFERENCES food_items (id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_logs_user_date ON user_meal_logs (user_id, logged_at);
CREATE INDEX IF NOT EXISTS idx_logs_meal_type ON user_meal_logs (meal_type);


CREATE TABLE IF NOT EXISTS weight_logs (
  id        TEXT     NOT NULL,
  user_id   TEXT     NOT NULL,
  weight_kg REAL     NOT NULL,
  logged_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  notes     TEXT,
  PRIMARY KEY (id),
  FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_weight_user_date ON weight_logs (user_id, logged_at);


CREATE TABLE IF NOT EXISTS chat_sessions (
  id         TEXT     NOT NULL,
  user_id    TEXT     NOT NULL,
  title      TEXT,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON chat_sessions (user_id);


CREATE TABLE IF NOT EXISTS chat_messages (
  id            TEXT     NOT NULL,
  session_id    TEXT     NOT NULL,
  user_id       TEXT     NOT NULL,
  user_query    TEXT     NOT NULL,
  chat_response TEXT     NOT NULL,
  created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE,
  FOREIGN KEY (user_id)    REFERENCES users          (id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_messages_session ON chat_messages (session_id);


CREATE TABLE IF NOT EXISTS refresh_tokens (
  id         TEXT     NOT NULL,
  user_id    TEXT     NOT NULL,
  token_hash TEXT     NOT NULL,
  expires_at DATETIME NOT NULL,
  revoked    INTEGER  NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE (token_hash),
  FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens (user_id);

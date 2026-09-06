# CalorieQ — Database Entities

**Database: MySQL 8+**

All timestamps are stored as `DATETIME` in UTC, precise to seconds. No bare `DATE` columns except `dob` (a calendar date by nature, not a point in time). IDs are `CHAR(36)` UUIDs generated at the application layer.

---

## 1. `users`
Auth and identity.

| Column | Type | Notes |
|---|---|---|
| `id` | CHAR(36) PK | UUID |
| `email` | VARCHAR(255) UNIQUE NOT NULL | |
| `password_hash` | TEXT NOT NULL | |
| `display_name` | VARCHAR(255) | |
| `created_at` | DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP | UTC |
| `updated_at` | DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | UTC |

→ *Req: Multi-User Support*

---

## 2. `user_profiles`
Physical stats for BMR/TDEE context in reports. Current weight is not stored here — derive it from the latest row in `weight_logs`.

| Column | Type | Notes |
|---|---|---|
| `user_id` | CHAR(36) PK FK → users | UUID |
| `dob` | DATE | calendar date, no time component needed |
| `gender` | VARCHAR(50) | |
| `height_cm` | DECIMAL(5,2) | |
| `activity_level` | VARCHAR(50) | sedentary / lightly_active / active / very_active |
| `updated_at` | DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | UTC |

→ *Req: Goal Setting, Reports*

---

## 3. `goals`
Versioned health targets — a new row is inserted when the user updates goals so history is preserved.

`goal_type` is a MySQL **ENUM**. Current values: `lose / maintain / gain`. Add new values via a schema migration — do not widen to free text.

| Column | Type | Notes |
|---|---|---|
| `id` | CHAR(36) PK | UUID |
| `user_id` | CHAR(36) FK → users | |
| `goal_type` | ENUM('lose','maintain','gain') NOT NULL | extend via migration |
| `daily_calories` | DECIMAL(7,2) | kcal |
| `protein_g` | DECIMAL(6,2) | |
| `carbs_g` | DECIMAL(6,2) | |
| `fat_g` | DECIMAL(6,2) | |
| `fibre_g` | DECIMAL(6,2) | |
| `weight_target_kg` | DECIMAL(5,2) | |
| `active_from` | DATETIME NOT NULL | UTC |
| `active_to` | DATETIME | UTC — NULL means currently active |
| `created_at` | DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP | UTC |

→ *Req: Goal Setting, Goal vs Actual charts*

---

## 4. `food_items`
Unified food database seeded from INDB (1,014 Indian recipes) and USDA SR Legacy (7,793 raw ingredients). Extended by user-created custom entries.

All nutrient values are **per 100 g**.

| Column | Type | Notes |
|---|---|---|
| `id` | CHAR(36) PK | UUID |
| `source` | VARCHAR(20) | indb / usda / user_custom |
| `external_id` | VARCHAR(50) | food_code (INDB) or fdc_id (USDA) |
| `name` | VARCHAR(500) NOT NULL | |
| `category` | VARCHAR(255) | |
| `energy_kcal` | DECIMAL(7,2) | |
| `energy_kj` | DECIMAL(7,2) | |
| `protein_g` | DECIMAL(6,2) | |
| `carb_g` | DECIMAL(6,2) | |
| `fat_g` | DECIMAL(6,2) | |
| `freesugar_g` | DECIMAL(6,2) | NULL for USDA entries (no direct equivalent) |
| `fibre_g` | DECIMAL(6,2) | |
| `sfa_g` | DECIMAL(6,2) | saturated fatty acids |
| `mufa_g` | DECIMAL(6,2) | monounsaturated fatty acids |
| `pufa_g` | DECIMAL(6,2) | polyunsaturated fatty acids |
| `cholesterol_mg` | DECIMAL(7,2) | |
| `calcium_mg` | DECIMAL(7,2) | |
| `phosphorus_mg` | DECIMAL(7,2) | |
| `magnesium_mg` | DECIMAL(7,2) | |
| `sodium_mg` | DECIMAL(7,2) | |
| `potassium_mg` | DECIMAL(7,2) | |
| `iron_mg` | DECIMAL(7,4) | |
| `copper_mg` | DECIMAL(7,4) | |
| `selenium_ug` | DECIMAL(7,4) | |
| `chromium_mg` | DECIMAL(7,4) | USDA: Chromium,Cr (id 1096, µg ÷ 1000) |
| `manganese_mg` | DECIMAL(7,4) | |
| `molybdenum_mg` | DECIMAL(7,4) | USDA: Molybdenum,Mo (id 1102, µg ÷ 1000) |
| `zinc_mg` | DECIMAL(7,4) | |
| `vita_ug` | DECIMAL(7,2) | Vitamin A RAE |
| `vite_mg` | DECIMAL(7,4) | Vitamin E (alpha-tocopherol) |
| `vitd2_ug` | DECIMAL(7,4) | Vitamin D2 |
| `vitd3_ug` | DECIMAL(7,4) | Vitamin D3 |
| `vitk1_ug` | DECIMAL(7,4) | Vitamin K1 (phylloquinone) |
| `vitk2_ug` | DECIMAL(7,4) | Vitamin K2 (MK-4 only in USDA) |
| `folate_ug` | DECIMAL(7,2) | Folate total |
| `vitb1_mg` | DECIMAL(7,4) | Thiamin |
| `vitb2_mg` | DECIMAL(7,4) | Riboflavin |
| `vitb3_mg` | DECIMAL(7,4) | Niacin |
| `vitb5_mg` | DECIMAL(7,4) | Pantothenic acid |
| `vitb6_mg` | DECIMAL(7,4) | |
| `vitb7_ug` | DECIMAL(7,4) | Biotin — USDA id 1176 |
| `vitb9_ug` | DECIMAL(7,4) | Folic acid |
| `vitc_mg` | DECIMAL(7,2) | |
| `carotenoids_ug` | DECIMAL(7,2) | USDA: sum of beta-carotene(1107) + alpha-carotene(1108) + lycopene(1122) + lutein+zeaxanthin(1123) |
| `is_verified` | BOOLEAN DEFAULT 1 | 0 for user_custom until reviewed |
| `created_by` | CHAR(36) FK → users | NULL for seeded entries |
| `created_at` | DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP | UTC |

→ *Req: Meal Entry, AI Extraction pre-fill*

---

## 5. `food_portions`
Named portion options per food item with gram weights. USDA SR Legacy supplies these from `food_portion.csv` (e.g. "1 medium banana" → 118 g, "1 cup milk" → 244 g). At log time the user picks a portion; gram conversion happens client/server side.

| Column | Type | Notes |
|---|---|---|
| `id` | CHAR(36) PK | UUID |
| `food_item_id` | CHAR(36) NOT NULL FK → food_items | |
| `description` | VARCHAR(255) NOT NULL | e.g. "1 cup", "1 medium", "1 large" |
| `gram_weight` | DECIMAL(7,2) NOT NULL | grams for this portion |
| `created_at` | DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP | UTC |

→ *Req: Meal Entry — quantity unit conversion*

---

## 6. `user_meal_logs`
Core meal logging table. Key macros denormalized at time of logging so report queries are fast and past entries are unaffected by edits to `food_items`. Micronutrient reports join back to `food_items` via `food_item_id`.

`source` distinguishes whether the entry was created by the user manually or by an AI feature (image extraction, chat, PDF import).

| Column | Type | Notes |
|---|---|---|
| `id` | CHAR(36) PK | UUID |
| `user_id` | CHAR(36) FK → users | |
| `food_item_id` | CHAR(36) FK → food_items | nullable — AI entries may not resolve to a known item |
| `logged_at` | DATETIME NOT NULL | UTC — when the meal was consumed |
| `meal_type` | VARCHAR(20) NOT NULL | breakfast / lunch / dinner / snacks |
| `food_name_snapshot` | VARCHAR(500) NOT NULL | name at time of logging |
| `quantity_g` | DECIMAL(7,2) NOT NULL | grams consumed |
| `energy_kcal` | DECIMAL(7,2) NOT NULL | scaled to quantity |
| `protein_g` | DECIMAL(6,2) NOT NULL | scaled to quantity |
| `carb_g` | DECIMAL(6,2) NOT NULL | scaled to quantity |
| `fat_g` | DECIMAL(6,2) NOT NULL | scaled to quantity |
| `fibre_g` | DECIMAL(6,2) | scaled to quantity |
| `sodium_mg` | DECIMAL(7,2) | scaled to quantity |
| `source` | VARCHAR(10) NOT NULL | user / ai |
| `notes` | TEXT | |
| `created_at` | DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP | UTC |

→ *Req: Meal Entry, Time-Range Listing, All Reports*

---

## 7. `weight_logs`
Tracks weight over time for goal vs actual charts. Latest row here is the user's current weight.

| Column | Type | Notes |
|---|---|---|
| `id` | CHAR(36) PK | UUID |
| `user_id` | CHAR(36) FK → users | |
| `weight_kg` | DECIMAL(5,2) NOT NULL | |
| `logged_at` | DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP | UTC |
| `notes` | TEXT | |

→ *Req: Reports — weight goal tracking*

---

## 8. `chat_sessions`
Container for a conversation thread.

| Column | Type | Notes |
|---|---|---|
| `id` | CHAR(36) PK | UUID |
| `user_id` | CHAR(36) FK → users | |
| `title` | VARCHAR(500) | auto-generated or user-set |
| `created_at` | DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP | UTC |
| `updated_at` | DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | UTC |

→ *Req: Conversational Chat Interface*

---

## 9. `chat_messages`
Stores user query and assistant response as a pair per turn.

> **Future:** LangGraph's checkpoint/persistence layer can replace this table for full multi-turn memory with tool history and long-term personalization.

| Column | Type | Notes |
|---|---|---|
| `id` | CHAR(36) PK | UUID |
| `session_id` | CHAR(36) FK → chat_sessions | |
| `user_id` | CHAR(36) FK → users | |
| `user_query` | TEXT NOT NULL | |
| `chat_response` | TEXT NOT NULL | |
| `created_at` | DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP | UTC |

→ *Req: Conversational Chat Interface*

---

## Data Sources Summary

| Source | Items | Coverage |
|---|---|---|
| INDB | 1,014 | Indian recipes (macros + 30 micros per 100 g) |
| USDA SR Legacy | 7,793 | Raw ingredients (macros + 37 micros per 100 g + portion weights) |
| User custom | — | Created at runtime via manual entry or AI extraction |

Gaps covered at runtime: branded/packaged foods (AI label scan), restaurant foods (manual entry or AI), non-Indian recipes (AI chat logging).

# CalorieQ — API Specification

**Version:** v1  
**Base URL:** `/api/v1`  
**Auth:** All endpoints except `/auth/register` and `/auth/login` require `Authorization: Bearer <access_token>`

---

## Conventions

### Authentication

`HTTPBearer` scheme. The Swagger `/docs` page shows a single **Authorize** dialog — paste the raw `access_token` (no `Bearer ` prefix needed in the input field).

### Pagination

List endpoints accept `?page=` (default `1`) and `?page_size=` (default `10`).

**Response envelope:**
```json
{
  "data": [],
  "meta": { "page": 1, "page_size": 10, "total": 84, "total_pages": 9 }
}
```

### Dates & Timezones

- All timestamps stored as **naive UTC** in SQLite and returned in ISO 8601.
- `logged_at` values sent with a timezone offset (e.g. `+05:30`) are converted to UTC before storage.
- Date-filtered endpoints (`/meals`, `/reports/*`) accept a `tz` param (IANA string, e.g. `Asia/Kolkata`). Day boundaries are resolved in the user's timezone so "today" means the correct local day.
- `start`/`end` on `/meals` accept either `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS[±offset]`.

### Error Responses

```json
{ "error": { "code": "NOT_FOUND", "message": "Food item not found" } }
```

| Status | Code | When |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Invalid request body / params |
| 401 | `UNAUTHORIZED` | Missing or invalid token |
| 403 | `FORBIDDEN` | Not allowed (e.g. editing another user's resource) |
| 404 | `NOT_FOUND` | Resource does not exist |
| 409 | `CONFLICT` | Duplicate (email, referenced food item) |
| 422 | `UNPROCESSABLE` | Business rule violation |

### Numeric bounds

All input limits are defined in `app/core/constraints.py`. Key values:

| Field | Limit |
|---|---|
| `quantity_g` | 0 < x < 2,000 g |
| `energy_kcal` (meal) | 0 ≤ x < 20,000 kcal |
| `daily_calories` (goal) | 0 < x < 15,000 kcal |
| `weight_kg` | 20 < x < 500 kg |
| `height_cm` | 50 < x < 250 cm |
| food search `page_size` | max 20 |
| report range | max 90 days |

---

## Auth

### POST `/auth/register`
**Request**
```json
{ "email": "user@example.com", "password": "min8chars", "display_name": "Yash" }
```
**Response `201`**
```json
{
  "user": { "id": "uuid", "email": "...", "display_name": "Yash", "created_at": "...", "updated_at": "..." },
  "access_token": "eyJ...", "refresh_token": "...", "token_type": "bearer", "expires_in": 86400
}
```
**Errors:** `400` short password / invalid email, `409` email taken

---

### POST `/auth/login`
**Request** `{ "email": "...", "password": "..." }`  
**Response `200`** `{ "access_token", "refresh_token", "token_type": "bearer", "expires_in": 86400 }`  
**Errors:** `401`

---

### POST `/auth/refresh`
**Request** `{ "refresh_token": "..." }`  
**Response `200`** New token pair. Old refresh token is immediately revoked (rotation).  
**Errors:** `401` revoked or expired

---

### POST `/auth/logout`
**Request** `{ "refresh_token": "..." }`  
**Response `204`** — Revokes the refresh token. Unknown tokens are silently ignored.

---

## Users

### GET `/users/me`
**Response `200`** `{ "id", "email", "display_name", "created_at", "updated_at" }`

---

### PATCH `/users/me`
**Request** `{ "display_name": "New Name" }` — all fields optional  
**Response `200`** Updated user object

---

### GET `/users/me/profile`
**Response `200`**
```json
{
  "dob": "1995-06-15", "gender": "male", "height_cm": 175.5,
  "activity_level": "lightly_active", "current_weight_kg": 78.5,
  "updated_at": "2024-01-15T08:00:00"
}
```
`current_weight_kg` is the latest `weight_logs` entry, not a stored profile field.  
`updated_at` is `null` if the profile has never been set.

---

### PATCH `/users/me/profile`
**Request** — all fields optional
```json
{
  "dob": "1995-06-15",
  "gender": "male | female | other | prefer_not_to_say",
  "height_cm": 175.5,
  "activity_level": "sedentary | lightly_active | active | very_active",
  "current_weight_kg": 78.5
}
```
`current_weight_kg` creates a new `weight_logs` entry — does not overwrite; history is preserved.  
Empty body `{}` is a no-op (no DB write, no `updated_at` bump).  
**Response `200`** Updated profile object

---

## Goals

Goals are **versioned** — creating a new goal closes the previous one (`active_to` is set). Only one goal has `active_to: null` at a time.

### POST `/goals`
**Request**
```json
{
  "goal_type": "lose | maintain | gain",
  "daily_calories": 1800.0,
  "protein_g": 140.0, "carbs_g": 180.0, "fat_g": 55.0, "fibre_g": 30.0,
  "weight_target_kg": 72.0
}
```
All nutrient fields optional.  
**Response `201`** `{ "id", "goal_type", "daily_calories", "protein_g", "carbs_g", "fat_g", "fibre_g", "weight_target_kg", "active_from", "active_to" }`

---

### GET `/goals/active`
**Response `200`** Active goal object  
**Response `404`** No goal has ever been set

---

### GET `/goals/history`
**Query:** `page`, `page_size`  
**Response `200`** Paginated list, newest first

---

## Food Items

### GET `/food_items`
Search the food database. Returns lightweight projection (no full micronutrient data).

**Query params:**

| Param | Notes |
|---|---|
| `q` | Name search (case-insensitive ILIKE) |
| `source` | `indb` \| `usda` \| `user_custom` |
| `page`, `page_size` | Max page_size = 20 |

**Response `200`** Paginated list: `{ "id", "source", "name", "category", "energy_kcal", "protein_g", "carb_g", "fat_g", "fibre_g" }`

---

### GET `/food_items/{id}`
Full nutrient detail (all 40 nutrient columns) + `portions` array.

**Response `200`**
```json
{
  "id": "uuid", "source": "indb", "name": "Dal Makhani", "category": "Legumes",
  "energy_kcal": 131.5, "protein_g": 6.2, "carb_g": 15.3, "fat_g": 5.1,
  "fibre_g": 3.8, "sodium_mg": 210.0, "...all 40 nutrient fields...",
  "is_verified": true,
  "portions": [{ "id": "uuid", "description": "1 cup", "gram_weight": 240.0 }]
}
```
**Errors:** `404`

---

### POST `/food_items`
Create a `user_custom` food item. All nutrient fields optional except `name` and `energy_kcal`.

**Response `201`** Full food item object with `is_verified: false`

---

### PATCH `/food_items/{id}`
Edit own `user_custom` food.  
**Errors:** `403` if `source != user_custom` or belongs to another user, `404`

---

### DELETE `/food_items/{id}`
Delete own `user_custom` food.  
**Errors:** `403` source not user_custom, `409` referenced by a meal log, `404`

---

## Meals

### POST `/meals`

**Linked entry** (server scales macros from food item's per-100g values):
```json
{ "food_item_id": "uuid", "meal_type": "lunch", "quantity_g": 250.0, "logged_at": "2024-01-15T13:30:00Z", "notes": "..." }
```

**Free-form entry** (client provides nutrition directly — for AI-extracted or unrecognised foods):
```json
{
  "food_name_snapshot": "Restaurant Biryani", "meal_type": "dinner",
  "quantity_g": 400.0, "energy_kcal": 520.0, "protein_g": 18.0,
  "carb_g": 72.0, "fat_g": 16.0, "source": "ai"
}
```

`meal_type` values: `breakfast | lunch | dinner | snacks`  
`logged_at` optional — defaults to `now()`. Accepts any ISO 8601 offset; converted to UTC on storage.  
**Response `201`** Meal log object

---

### GET `/meals/history`
**Query params:**

| Param | Notes |
|---|---|
| `date` | `YYYY-MM-DD` — whole day shortcut. Defaults to today. |
| `start` | `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS[±offset]` — range start (inclusive) |
| `end` | `YYYY-MM-DD` or `YYYY-MM-DDTHH:MM:SS[±offset]` — range end. Date is end-inclusive; datetime is exclusive. |
| `tz` | IANA timezone (default `UTC`) — used to resolve day boundaries |
| `meal_type` | Optional filter |
| `page`, `page_size` | |

`date` and `start/end` are mutually exclusive. `start` requires `end`.

**Response `200`** Paginated list of meal log objects, newest first

---

### GET `/meals/{id}`
**Response `200`** Single meal log  
**Errors:** `403`, `404`

---

### PATCH `/meals/{id}`
**Linked entries:** `quantity_g`, `meal_type`, `logged_at`, `notes` — macros auto-recalculated on quantity change.  
**Free-form entries:** above fields + direct nutrition overrides (`energy_kcal`, `protein_g`, etc.).

**Response `200`** Updated meal log  
**Errors:** `403`, `404`

---

### DELETE `/meals/{id}`
**Response `204`**  
**Errors:** `403`, `404`

---

## Reports

All report endpoints require `tz` (IANA timezone, default `UTC`). Responses do **not** echo `tz` back — client already has it.

### GET `/reports/daily_summary`
Primary dashboard call. Single-day totals vs active goal.

**Query:** `date=YYYY-MM-DD` (default today), `tz=`

**Response `200`**
```json
{
  "date": "2024-01-15",
  "goal": { "daily_calories": 1800, "protein_g": 140, "carbs_g": 180, "fat_g": 60, "fibre_g": 30, "weight_target_kg": 72 },
  "consumed": { "energy_kcal": 1240, "protein_g": 89.5, "carb_g": 130.2, "fat_g": 38.1, "fibre_g": 18.6 },
  "remaining": { "energy_kcal": 560, "protein_g": 50.5, "carbs_g": 49.8, "fat_g": 21.9 },
  "meals_tracked": 2
}
```
`goal` and `remaining` are `null` if no goal has been set. `remaining` can be negative (exceeded goal).

---

### GET `/reports/weekly`
Replaces `weekly_calories` + `macros` + `goal_vs_actual` — one call covers all weekly charts.

**Query:** `week_of=YYYY-MM-DD` (snaps to containing Sun–Sat week) **or** `start=YYYY-MM-DD&end=YYYY-MM-DD`, plus `tz=`  
Max range: 90 days.

**Response `200`**
```json
{
  "start": "2024-01-14", "end": "2024-01-20",
  "days_with_logs": 5,
  "goal": { "daily_calories": 1800, "..." },
  "actual_period_avg": { "energy_kcal": 1953, "protein_g": 125.4, "carb_g": 198.3, "fat_g": 64.1, "fibre_g": 28 },
  "data": [
    { "date": "2024-01-14", "energy_kcal": 0.0, "protein_g": 0.0, "carb_g": 0.0, "fat_g": 0.0, "fibre_g": 0.0 },
    { "date": "2024-01-15", "energy_kcal": 1850.0, "..." }
  ],
  "weight_logs": [{ "logged_at": "2024-01-14T07:00:00", "weight_kg": 80.2 }]
}
```

- Days with no logs are zero-filled — no gaps in charts.
- `actual_period_avg` divides by `days_with_logs` only (not total days in range).
- `goal` uses the most recently set goal that started on or before the end of the period.

---

### GET `/reports/micros`
Micronutrient totals for a period. **Only linked entries** (with `food_item_id`) contribute — free-form entries have no food item reference for micro data.

**Query:** same as `/reports/weekly`

**Response `200`**
```json
{
  "start": "2024-01-14", "end": "2024-01-20",
  "note": "Free-form entries without a linked food item are excluded...",
  "totals": {
    "calcium_mg": 3850.0, "iron_mg": 84.2, "vitc_mg": 312.0, "vitd2_ug": null, "..."
  }
}
```
`null` means no logged food item had data for that nutrient in the period.

---

## Not yet implemented

The following endpoints are designed and specified but not yet built:

| Endpoint | Feature |
|---|---|
| `POST /weight_logs`, `GET /weight_logs` | Standalone weight log CRUD |
| `DELETE /users/me` | Account deletion |
| `POST /ai/extract_image` | Bedrock vision → nutrition pre-fill |
| `POST /ai/import_pdf` | PDF diary → bulk meal import |
| `POST /chat/sessions`, `GET /chat/sessions`, etc. | LangGraph chat agent |

---

## Endpoint Summary

| # | Method | Path | Auth |
|---|---|---|---|
| 1 | POST | `/auth/register` | ✗ |
| 2 | POST | `/auth/login` | ✗ |
| 3 | POST | `/auth/refresh` | ✗ |
| 4 | POST | `/auth/logout` | ✗ |
| 5 | GET | `/users/me` | ✓ |
| 6 | PATCH | `/users/me` | ✓ |
| 7 | GET | `/users/me/profile` | ✓ |
| 8 | PATCH | `/users/me/profile` | ✓ |
| 9 | POST | `/goals` | ✓ |
| 10 | GET | `/goals/active` | ✓ |
| 11 | GET | `/goals/history` | ✓ |
| 12 | GET | `/food_items` | ✓ |
| 13 | GET | `/food_items/{id}` | ✓ |
| 14 | POST | `/food_items` | ✓ |
| 15 | PATCH | `/food_items/{id}` | ✓ |
| 16 | DELETE | `/food_items/{id}` | ✓ |
| 17 | POST | `/meals` | ✓ |
| 18 | GET | `/meals/history` | ✓ |
| 19 | GET | `/meals/{id}` | ✓ |
| 20 | PATCH | `/meals/{id}` | ✓ |
| 21 | DELETE | `/meals/{id}` | ✓ |
| 22 | GET | `/reports/daily_summary` | ✓ |
| 23 | GET | `/reports/weekly` | ✓ |
| 24 | GET | `/reports/micros` | ✓ |

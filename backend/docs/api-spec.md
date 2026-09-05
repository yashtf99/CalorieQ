# CalorieQ — API Specification

**Version:** v1  
**Base URL:** `/api/v1`  
**Auth:** All endpoints except `/auth/register` and `/auth/login` require `Authorization: Bearer <access_token>`

---

## Conventions

### Pagination

All list endpoints accept `?page=` and `?page_size=` (default `10`, max `100`).

**Response envelope:**
```json
{
  "data": [],
  "meta": {
    "page": 1,
    "page_size": 10,
    "total": 84,
    "total_pages": 9
  }
}
```

### Dates & Timezones

- All timestamps stored in UTC, returned in ISO 8601: `"2024-01-15T08:30:00Z"`
- Date-filtered endpoints (`/meals`, `/reports/*`, `/weight_logs`) require a `tz` param (IANA timezone string, e.g. `Asia/Kolkata`, `America/New_York`) so date boundaries are computed correctly server-side
- Date-only params (`date=`) use `YYYY-MM-DD` format

### IDs

All resource IDs are UUIDs (`CHAR(36)`), e.g. `"a1b2c3d4-e5f6-..."`

### Error Responses

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Food item not found"
  }
}
```

| HTTP Status | code | When |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Invalid request body / params |
| 401 | `UNAUTHORIZED` | Missing or invalid token |
| 403 | `FORBIDDEN` | Authenticated but not allowed (e.g. editing another user's data) |
| 404 | `NOT_FOUND` | Resource does not exist |
| 409 | `CONFLICT` | Duplicate (e.g. email already registered) |
| 422 | `UNPROCESSABLE` | Business rule violation (e.g. negative calories) |
| 500 | `INTERNAL_ERROR` | Unexpected server error |

---

## Auth

### POST `/auth/register`

Create a new account.

**Request**
```json
{
  "email": "user@example.com",
  "password": "min8chars",
  "display_name": "Yash"
}
```

**Response `201`**
```json
{
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "display_name": "Yash",
    "created_at": "2024-01-15T08:00:00Z"
  },
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Errors:** `400` invalid body, `409` email already registered

---

### POST `/auth/login`

**Request**
```json
{
  "email": "user@example.com",
  "password": "min8chars"
}
```

**Response `200`**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Errors:** `401` invalid credentials

---

### POST `/auth/refresh`

Exchange a refresh token for a new access + refresh token pair. The submitted refresh token is immediately invalidated (rotation).

**Request**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response `200`**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**Errors:** `401` token invalid or already revoked

---

### POST `/auth/logout`

Revoke the current refresh token server-side. Access token runs out naturally (24 h).

**Request**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response `204`** — no body

---

## Users

### GET `/users/me`

**Response `200`**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "display_name": "Yash",
  "created_at": "2024-01-15T08:00:00Z",
  "updated_at": "2024-01-15T08:00:00Z"
}
```

---

### PATCH `/users/me`

**Request** — all fields optional
```json
{
  "display_name": "Yash M"
}
```

**Response `200`** — updated user object (same shape as GET)

---

### DELETE `/users/me`

Permanently deletes the account and all associated data (meals, goals, weight logs, chat sessions). Irreversible.

**Request**
```json
{
  "password": "confirm-current-password"
}
```

**Response `204`** — no body

**Errors:** `401` wrong password

---

### GET `/users/me/profile`

Physical stats used for BMR/TDEE context in reports.

**Response `200`**
```json
{
  "user_id": "uuid",
  "dob": "1995-06-15",
  "gender": "male",
  "height_cm": 175.5,
  "activity_level": "lightly_active",
  "updated_at": "2024-01-15T08:00:00Z"
}
```

`activity_level` values: `sedentary` | `lightly_active` | `active` | `very_active`

---

### PATCH `/users/me/profile`

**Request** — all fields optional
```json
{
  "dob": "1995-06-15",
  "gender": "male",
  "height_cm": 175.5,
  "activity_level": "lightly_active"
}
```

**Response `200`** — updated profile object (same shape as GET)

---

## Goals

### POST `/goals`

Create a new goal. Server sets `active_from = now()` and closes the previously active goal by setting its `active_to = now()`.

**Request**
```json
{
  "goal_type": "lose",
  "daily_calories": 1800.0,
  "protein_g": 140.0,
  "carbs_g": 180.0,
  "fat_g": 60.0,
  "fibre_g": 30.0,
  "weight_target_kg": 72.0
}
```

`goal_type` values: `lose` | `maintain` | `gain`  
All nutrient fields are optional — set only what the user cares about tracking.

**Response `201`**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "goal_type": "lose",
  "daily_calories": 1800.0,
  "protein_g": 140.0,
  "carbs_g": 180.0,
  "fat_g": 60.0,
  "fibre_g": 30.0,
  "weight_target_kg": 72.0,
  "active_from": "2024-01-15T08:00:00Z",
  "active_to": null,
  "created_at": "2024-01-15T08:00:00Z"
}
```

---

### GET `/goals/active`

Returns the currently active goal (`active_to IS NULL`).

**Response `200`** — goal object (same shape as POST response)

**Response `404`** — user has never set a goal

---

### GET `/goals/history`

All goal rows for the user, newest first.

**Query params:** `page`, `page_size`

**Response `200`** — paginated list of goal objects

---

## Food Items

### GET `/food_items`

Search the food database. Returns a lightweight projection (no full micronutrient data).

**Query params:**

| Param | Type | Notes |
|---|---|---|
| `q` | string | Full-text search on name. Required if `source` not set. |
| `source` | string | Filter: `indb` \| `usda` \| `user_custom` |
| `page` | int | Default 1 |
| `page_size` | int | Default 10, max 50 |

**Response `200`**
```json
{
  "data": [
    {
      "id": "uuid",
      "source": "indb",
      "name": "Dal Makhani",
      "category": "Legumes",
      "energy_kcal": 131.5,
      "protein_g": 6.2,
      "carb_g": 15.3,
      "fat_g": 5.1,
      "fibre_g": 3.8
    }
  ],
  "meta": { "page": 1, "page_size": 10, "total": 38, "total_pages": 4 }
}
```

---

### GET `/food_items/{id}`

Full nutrient detail for one food item, including all micros and available portions.

**Response `200`**
```json
{
  "id": "uuid",
  "source": "indb",
  "external_id": "ASC001",
  "name": "Dal Makhani",
  "category": "Legumes",
  "energy_kcal": 131.5,
  "energy_kj": 550.2,
  "protein_g": 6.2,
  "carb_g": 15.3,
  "fat_g": 5.1,
  "freesugar_g": null,
  "fibre_g": 3.8,
  "sfa_g": 1.2,
  "mufa_g": 2.1,
  "pufa_g": 0.8,
  "cholesterol_mg": 8.0,
  "calcium_mg": 48.0,
  "phosphorus_mg": 112.0,
  "magnesium_mg": 28.0,
  "sodium_mg": 210.0,
  "potassium_mg": 305.0,
  "iron_mg": 2.1,
  "copper_mg": 0.18,
  "selenium_ug": 3.2,
  "chromium_mg": null,
  "manganese_mg": 0.42,
  "molybdenum_mg": null,
  "zinc_mg": 0.9,
  "vita_ug": 12.0,
  "vite_mg": 0.5,
  "vitd2_ug": null,
  "vitd3_ug": null,
  "vitk1_ug": 8.0,
  "vitk2_ug": null,
  "folate_ug": 42.0,
  "vitb1_mg": 0.12,
  "vitb2_mg": 0.08,
  "vitb3_mg": 1.1,
  "vitb5_mg": 0.3,
  "vitb6_mg": 0.15,
  "vitb7_ug": null,
  "vitb9_ug": null,
  "vitc_mg": 1.5,
  "carotenoids_ug": 72.0,
  "is_verified": true,
  "created_by": null,
  "created_at": "2024-01-01T00:00:00Z",
  "portions": [
    {
      "id": "uuid",
      "description": "1 cup",
      "gram_weight": 240.0
    }
  ]
}
```

**Errors:** `404`

---

### POST `/food_items`

Create a user-defined custom food. `source` is always set to `user_custom` server-side.

**Request**
```json
{
  "name": "Mom's Khichdi",
  "category": "Rice dishes",
  "energy_kcal": 120.0,
  "protein_g": 4.5,
  "carb_g": 22.0,
  "fat_g": 2.0,
  "fibre_g": 1.5,
  "sodium_mg": 180.0
}
```

All nutrient fields optional except `name` and `energy_kcal`.

**Response `201`** — full food item object with `is_verified: false`

---

### PATCH `/food_items/{id}`

Edit a `user_custom` food item. Only the creating user can edit it.

**Request** — all fields optional, same shape as POST

**Response `200`** — updated food item object

**Errors:** `403` if `source != user_custom` or item belongs to another user, `404`

---

### DELETE `/food_items/{id}`

Delete a `user_custom` food item. Fails if it is referenced by any meal log.

**Response `204`** — no body

**Errors:** `403` if `source != user_custom`, `409` if referenced by meal logs, `404`

---

## Meals

### POST `/meals`

Log a meal entry. Server fetches the food item's per-100g values and scales them to `quantity_g`.

**Request**
```json
{
  "food_item_id": "uuid",
  "meal_type": "lunch",
  "quantity_g": 250.0,
  "logged_at": "2024-01-15T13:30:00Z",
  "notes": "Added extra ghee"
}
```

`meal_type` values: `breakfast` | `lunch` | `dinner` | `snacks`  
`food_item_id` is optional — omit for free-form entries (AI-sourced) where no food item is resolved. If omitted, nutrition values must be provided directly in the request body.

**Request (free-form — no food_item_id)**
```json
{
  "food_name_snapshot": "Restaurant Biryani",
  "meal_type": "dinner",
  "quantity_g": 400.0,
  "logged_at": "2024-01-15T20:00:00Z",
  "energy_kcal": 520.0,
  "protein_g": 18.0,
  "carb_g": 72.0,
  "fat_g": 16.0,
  "source": "ai"
}
```

**Response `201`**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "food_item_id": "uuid",
  "food_name_snapshot": "Dal Makhani",
  "meal_type": "lunch",
  "quantity_g": 250.0,
  "energy_kcal": 328.75,
  "protein_g": 15.5,
  "carb_g": 38.25,
  "fat_g": 12.75,
  "fibre_g": 9.5,
  "sodium_mg": 525.0,
  "source": "user",
  "notes": "Added extra ghee",
  "logged_at": "2024-01-15T13:30:00Z",
  "created_at": "2024-01-15T13:31:00Z"
}
```

**Errors:** `404` food item not found, `422` invalid nutrition values (negative calories etc.)

---

### GET `/meals`

List meal entries. Defaults to today in the user's timezone if no date params are given.

**Query params:**

| Param | Type | Notes |
|---|---|---|
| `date` | YYYY-MM-DD | Single day. Mutually exclusive with `start`/`end`. |
| `start` | YYYY-MM-DD | Range start (inclusive). Use with `end`. |
| `end` | YYYY-MM-DD | Range end (inclusive). Use with `start`. |
| `tz` | IANA string | Required when any date param is set. e.g. `Asia/Kolkata` |
| `meal_type` | string | Optional filter: `breakfast` \| `lunch` \| `dinner` \| `snacks` |
| `page` | int | Default 1 |
| `page_size` | int | Default 10 |

**Response `200`** — paginated list of meal objects (same shape as POST response)

---

### GET `/meals/{id}`

**Response `200`** — single meal object

**Errors:** `403` if belongs to another user, `404`

---

### PATCH `/meals/{id}`

Edit a logged meal. If `quantity_g` is updated and `food_item_id` is set, server recalculates all macros from the food item's per-100g values.

**Request** — all fields optional
```json
{
  "quantity_g": 300.0,
  "meal_type": "dinner",
  "logged_at": "2024-01-15T20:00:00Z",
  "notes": "Updated portion"
}
```

**Response `200`** — updated meal object with recalculated macros

**Errors:** `403`, `404`

---

### DELETE `/meals/{id}`

**Response `204`** — no body

**Errors:** `403`, `404`

---

## Weight Logs

### POST `/weight_logs`

**Request**
```json
{
  "weight_kg": 78.5,
  "logged_at": "2024-01-15T07:00:00Z",
  "notes": "Morning, after workout"
}
```

`logged_at` is optional — defaults to `now()`.

**Response `201`**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "weight_kg": 78.5,
  "logged_at": "2024-01-15T07:00:00Z",
  "notes": "Morning, after workout"
}
```

---

### GET `/weight_logs`

**Query params:** `start` (YYYY-MM-DD), `end` (YYYY-MM-DD), `tz`, `page`, `page_size`

**Response `200`** — paginated list of weight log objects, newest first

---

## Reports

All report endpoints are read-only aggregations over the authenticated user's data. All require `tz`.

### GET `/reports/daily_summary`

Primary dashboard call. Returns today's totals vs the active goal.

**Query params:** `date` (YYYY-MM-DD, defaults to today), `tz`

**Response `200`**
```json
{
  "date": "2024-01-15",
  "goal": {
    "daily_calories": 1800.0,
    "protein_g": 140.0,
    "carbs_g": 180.0,
    "fat_g": 60.0,
    "fibre_g": 30.0
  },
  "consumed": {
    "energy_kcal": 1240.0,
    "protein_g": 89.5,
    "carb_g": 130.2,
    "fat_g": 38.1,
    "fibre_g": 18.6,
    "sodium_mg": 1850.0
  },
  "remaining": {
    "energy_kcal": 560.0,
    "protein_g": 50.5,
    "carbs_g": 49.8,
    "fat_g": 21.9
  },
  "meals_logged": 2
}
```

---

### GET `/reports/weekly_calories`

Daily calorie totals for a date range. Powers the weekly trend line chart.

**Query params:** `start` (YYYY-MM-DD), `end` (YYYY-MM-DD), `tz`

**Response `200`**
```json
{
  "start": "2024-01-09",
  "end": "2024-01-15",
  "data": [
    { "date": "2024-01-09", "energy_kcal": 1850.0 },
    { "date": "2024-01-10", "energy_kcal": 2100.0 },
    { "date": "2024-01-11", "energy_kcal": 0.0 },
    { "date": "2024-01-12", "energy_kcal": 1760.0 },
    { "date": "2024-01-13", "energy_kcal": 1920.0 },
    { "date": "2024-01-14", "energy_kcal": 2050.0 },
    { "date": "2024-01-15", "energy_kcal": 1240.0 }
  ],
  "goal_daily_calories": 1800.0
}
```

Days with no logs appear with `energy_kcal: 0.0` so the chart has no gaps.

---

### GET `/reports/macros`

Macro breakdown per day. Powers the stacked bar chart.

**Query params:** `start`, `end`, `tz`

**Response `200`**
```json
{
  "start": "2024-01-09",
  "end": "2024-01-15",
  "data": [
    {
      "date": "2024-01-09",
      "protein_g": 132.0,
      "carb_g": 210.5,
      "fat_g": 58.2,
      "fibre_g": 28.1
    }
  ]
}
```

---

### GET `/reports/micros`

Micronutrient totals for a period. Joins back to `food_items` for micro values (not denormalized on meal logs).

**Query params:** `start`, `end`, `tz`

**Response `200`**
```json
{
  "start": "2024-01-09",
  "end": "2024-01-15",
  "totals": {
    "calcium_mg": 3850.0,
    "iron_mg": 84.2,
    "vitc_mg": 312.0,
    "vitd2_ug": 0.0,
    "vitd3_ug": 4.2,
    "vitb12_ug": null
  }
}
```

`null` means no logged food item in this period had data for that micro.

---

### GET `/reports/goal_vs_actual`

Aggregate totals vs goal targets for a period.

**Query params:** `start`, `end`, `tz`

**Response `200`**
```json
{
  "start": "2024-01-09",
  "end": "2024-01-15",
  "days_with_logs": 6,
  "goal": {
    "daily_calories": 1800.0,
    "protein_g": 140.0,
    "carbs_g": 180.0,
    "fat_g": 60.0
  },
  "actual_daily_avg": {
    "energy_kcal": 1953.0,
    "protein_g": 125.4,
    "carb_g": 198.3,
    "fat_g": 64.1
  },
  "weight_logs": [
    { "logged_at": "2024-01-09T07:00:00Z", "weight_kg": 80.2 },
    { "logged_at": "2024-01-15T07:00:00Z", "weight_kg": 79.6 }
  ],
  "weight_target_kg": 72.0
}
```

---

## AI

### POST `/ai/extract_image`

Upload a food photo or nutrition label. Calls Bedrock synchronously — client waits for the response. Does **not** write any meal log — returns pre-fill data only. Client uses the result to pre-populate a meal log form, then calls `POST /meals` to confirm.

**Request** — `multipart/form-data`

| Field | Type | Notes |
|---|---|---|
| `image` | file | JPEG/PNG/WEBP, max 10 MB |
| `meal_type` | string | Optional hint passed to the model |

**Response `200`**
```json
{
  "food_name": "Amul Butter",
  "energy_kcal": 717.0,
  "protein_g": 0.5,
  "carb_g": 0.0,
  "fat_g": 79.5,
  "sodium_mg": 570.0,
  "quantity_g": 10.0,
  "confidence": "high"
}
```

`confidence` values: `high` | `medium` | `low` — reflects model certainty; surface to user when `low`.

**Errors:** `422` model could not extract nutrition from the image, `400` unsupported file type

---

### POST `/ai/import_pdf`

Upload a food diary PDF. Calls Bedrock synchronously — client waits. On success, meal entries are bulk-inserted into `user_meal_logs`. No confirmation step.

**Request** — `multipart/form-data`

| Field | Type | Notes |
|---|---|---|
| `pdf` | file | Max 20 MB |
| `tz` | string | Required — IANA timezone to interpret date columns in the PDF |

**Response `200`**
```json
{
  "imported": 42,
  "skipped": 3,
  "skipped_reasons": [
    "Row 12: unrecognised food name",
    "Row 28: missing date"
  ]
}
```

**Errors:** `422` PDF contains no parseable meal data

---

## Chat

### POST `/chat/sessions`

Start a new conversation session.

**Request** — body optional
```json
{
  "title": "Evening check-in"
}
```

If `title` is omitted, server generates one from the first message (updated on first `POST /messages`).

**Response `201`**
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "title": "Evening check-in",
  "created_at": "2024-01-15T20:00:00Z",
  "updated_at": "2024-01-15T20:00:00Z"
}
```

---

### GET `/chat/sessions`

**Query params:** `page`, `page_size`

**Response `200`** — paginated list of session objects, newest first

---

### GET `/chat/sessions/{id}`

**Response `200`** — single session object

**Errors:** `403`, `404`

---

### DELETE `/chat/sessions/{id}`

Deletes the session and all its messages.

**Response `204`** — no body

**Errors:** `403`, `404`

---

### GET `/chat/sessions/{id}/messages`

Message history for a session, oldest first (chronological for rendering).

**Query params:** `page`, `page_size`

**Response `200`**
```json
{
  "data": [
    {
      "id": "uuid",
      "session_id": "uuid",
      "user_id": "uuid",
      "user_query": "Log 200g of dal makhani for lunch",
      "chat_response": "Done! I've logged 200g of Dal Makhani for lunch — 263 kcal, 12.4g protein.",
      "created_at": "2024-01-15T13:00:00Z"
    }
  ],
  "meta": { "page": 1, "page_size": 10, "total": 5, "total_pages": 1 }
}
```

---

### POST `/chat/sessions/{id}/messages`

Send a message. The LangGraph agent runs to completion server-side — client waits for the full response. The user query and assistant response are persisted to `chat_messages` before the response is returned.

**Request**
```json
{
  "content": "Log 200g of dal makhani for lunch"
}
```

**Response `200`**
```json
{
  "id": "uuid",
  "session_id": "uuid",
  "user_id": "uuid",
  "user_query": "Log 200g of dal makhani for lunch",
  "chat_response": "Done! I've logged 200g of Dal Makhani for lunch — 263 kcal, 12.4g protein.",
  "created_at": "2024-01-15T13:00:00Z"
}
```

**Errors:** `403`, `404` session not found

---

## Endpoint Summary

| # | Method | Path |
|---|---|---|
| 1 | POST | `/auth/register` |
| 2 | POST | `/auth/login` |
| 3 | POST | `/auth/refresh` |
| 4 | POST | `/auth/logout` |
| 5 | GET | `/users/me` |
| 6 | PATCH | `/users/me` |
| 7 | DELETE | `/users/me` |
| 8 | GET | `/users/me/profile` |
| 9 | PATCH | `/users/me/profile` |
| 10 | POST | `/goals` |
| 11 | GET | `/goals/active` |
| 12 | GET | `/goals/history` |
| 13 | GET | `/food_items` |
| 14 | GET | `/food_items/{id}` |
| 15 | POST | `/food_items` |
| 16 | PATCH | `/food_items/{id}` |
| 17 | DELETE | `/food_items/{id}` |
| 18 | POST | `/meals` |
| 19 | GET | `/meals` |
| 20 | GET | `/meals/{id}` |
| 21 | PATCH | `/meals/{id}` |
| 22 | DELETE | `/meals/{id}` |
| 23 | POST | `/weight_logs` |
| 24 | GET | `/weight_logs` |
| 25 | GET | `/reports/daily_summary` |
| 26 | GET | `/reports/weekly_calories` |
| 27 | GET | `/reports/macros` |
| 28 | GET | `/reports/micros` |
| 29 | GET | `/reports/goal_vs_actual` |
| 30 | POST | `/ai/extract_image` |
| 31 | POST | `/ai/import_pdf` |
| 32 | POST | `/chat/sessions` |
| 33 | GET | `/chat/sessions` |
| 34 | GET | `/chat/sessions/{id}` |
| 35 | DELETE | `/chat/sessions/{id}` |
| 36 | GET | `/chat/sessions/{id}/messages` |
| 37 | POST | `/chat/sessions/{id}/messages` |

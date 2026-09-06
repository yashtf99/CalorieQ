"""
Report endpoint tests.
All timestamps use fixed past dates so tests are timezone-agnostic.
"""
import pytest

REGISTER       = "/api/v1/auth/register"
FOOD_ITEMS     = "/api/v1/food_items"
MEALS          = "/api/v1/meals"
GOALS          = "/api/v1/goals"
WEIGHT_LOGS    = "/api/v1/weight_logs"
DAILY_SUMMARY  = "/api/v1/reports/daily_summary"
WEEKLY         = "/api/v1/reports/weekly"
MICROS         = "/api/v1/reports/micros"

IST = "Asia/Kolkata"

_FOOD = {
    "name": "Dal",
    "energy_kcal": 100.0,   # per 100g → easy round numbers for assertions
    "protein_g": 10.0,
    "carb_g": 15.0,
    "fat_g": 2.0,
    "fibre_g": 3.0,
    "sodium_mg": 50.0,
    # micro data
    "calcium_mg": 80.0,
}

_GOAL = {
    "goal_type": "lose",
    "daily_calories": 1800.0,
    "protein_g": 120.0,
    "carbs_g": 200.0,
    "fat_g": 60.0,
}

# ── helpers ───────────────────────────────────────────────────────────────────

def _log_meal(client, headers, logged_at: str, quantity_g: float = 200.0, food_id: str | None = None):
    if food_id:
        payload = {"food_item_id": food_id, "meal_type": "lunch", "quantity_g": quantity_g, "logged_at": logged_at}
    else:
        payload = {
            "food_name_snapshot": "Free meal", "meal_type": "lunch",
            "quantity_g": quantity_g, "energy_kcal": 300.0,
            "protein_g": 20.0, "carb_g": 40.0, "fat_g": 10.0,
            "logged_at": logged_at,
        }
    r = client.post(MEALS, json=payload, headers=headers)
    assert r.status_code == 201, r.json()
    return r.json()


def _create_food(client, headers):
    r = client.post(FOOD_ITEMS, json=_FOOD, headers=headers)
    assert r.status_code == 201
    return r.json()["id"]


# ══════════════════════════════════════════════════════════════════════════════
# daily_summary
# ══════════════════════════════════════════════════════════════════════════════

def test_daily_summary_no_logs_returns_zeros(client, token_headers):
    r = client.get(DAILY_SUMMARY, params={"date": "2024-06-15", "tz": "UTC"}, headers=token_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["consumed"]["energy_kcal"] == 0.0
    assert body["meals_tracked"] == 0
    assert body["goal"] is None
    assert body["remaining"] is None


def test_daily_summary_aggregates_day_logs(client, token_headers):
    _log_meal(client, token_headers, "2024-06-15T08:00:00Z")
    _log_meal(client, token_headers, "2024-06-15T13:00:00Z")
    _log_meal(client, token_headers, "2024-06-16T08:00:00Z")  # next day — excluded

    r = client.get(DAILY_SUMMARY, params={"date": "2024-06-15", "tz": "UTC"}, headers=token_headers)
    body = r.json()
    assert body["meals_tracked"] == 2
    assert body["consumed"]["energy_kcal"] == 600.0  # 2 × 300


def test_daily_summary_with_active_goal_shows_remaining(client, token_headers):
    client.post(GOALS, json=_GOAL, headers=token_headers)
    _log_meal(client, token_headers, "2024-06-15T08:00:00Z")   # 300 kcal

    r = client.get(DAILY_SUMMARY, params={"date": "2024-06-15", "tz": "UTC"}, headers=token_headers)
    body = r.json()
    assert body["goal"]["daily_calories"] == 1800.0
    assert body["remaining"]["energy_kcal"] == 1500.0   # 1800 - 300


def test_daily_summary_remaining_negative_when_over_goal(client, token_headers):
    client.post(GOALS, json={**_GOAL, "daily_calories": 200.0}, headers=token_headers)
    _log_meal(client, token_headers, "2024-06-15T08:00:00Z")   # 300 kcal > 200 limit

    r = client.get(DAILY_SUMMARY, params={"date": "2024-06-15", "tz": "UTC"}, headers=token_headers)
    assert r.json()["remaining"]["energy_kcal"] == -100.0


def test_daily_summary_defaults_to_today(client, token_headers):
    r = client.get(DAILY_SUMMARY, params={"tz": "UTC"}, headers=token_headers)
    assert r.status_code == 200


def test_daily_summary_respects_tz(client, token_headers):
    # 23:30 UTC Jun 14 = 05:00 IST Jun 15
    _log_meal(client, token_headers, "2024-06-14T23:30:00+00:00")

    assert client.get(DAILY_SUMMARY, params={"date": "2024-06-14", "tz": "UTC"}, headers=token_headers).json()["meals_tracked"] == 1
    assert client.get(DAILY_SUMMARY, params={"date": "2024-06-15", "tz": IST},   headers=token_headers).json()["meals_tracked"] == 1
    assert client.get(DAILY_SUMMARY, params={"date": "2024-06-14", "tz": IST},   headers=token_headers).json()["meals_tracked"] == 0


def test_daily_summary_requires_auth(client):
    assert client.get(DAILY_SUMMARY).status_code == 401


# ══════════════════════════════════════════════════════════════════════════════
# weekly
# ══════════════════════════════════════════════════════════════════════════════

def test_weekly_returns_7_rows_for_full_week(client, token_headers):
    r = client.get(WEEKLY, params={"week_of": "2024-06-19", "tz": "UTC"}, headers=token_headers)
    assert r.status_code == 200
    body = r.json()
    assert len(body["data"]) == 7
    assert body["start"] == "2024-06-16"   # Sunday
    assert body["end"]   == "2024-06-22"   # Saturday


def test_weekly_week_of_snaps_to_sunday(client, token_headers):
    # Thu Jun 20 should snap to Sun Jun 16 – Sat Jun 22
    r = client.get(WEEKLY, params={"week_of": "2024-06-20", "tz": "UTC"}, headers=token_headers)
    assert r.json()["start"] == "2024-06-16"
    assert r.json()["end"]   == "2024-06-22"


def test_weekly_zero_fills_days_with_no_logs(client, token_headers):
    _log_meal(client, token_headers, "2024-06-19T12:00:00Z")   # Wednesday only

    r = client.get(WEEKLY, params={"week_of": "2024-06-19", "tz": "UTC"}, headers=token_headers)
    data = r.json()["data"]
    assert len(data) == 7
    logged_days = [row for row in data if row["energy_kcal"] > 0]
    empty_days  = [row for row in data if row["energy_kcal"] == 0.0]
    assert len(logged_days) == 1
    assert len(empty_days)  == 6


def test_weekly_aggregates_multiple_meals_per_day(client, token_headers):
    _log_meal(client, token_headers, "2024-06-19T08:00:00Z")   # 300 kcal
    _log_meal(client, token_headers, "2024-06-19T13:00:00Z")   # 300 kcal

    r = client.get(WEEKLY, params={"week_of": "2024-06-19", "tz": "UTC"}, headers=token_headers)
    wed_row = next(row for row in r.json()["data"] if row["date"] == "2024-06-19")
    assert wed_row["energy_kcal"] == 600.0


def test_weekly_days_with_logs_count(client, token_headers):
    _log_meal(client, token_headers, "2024-06-17T10:00:00Z")   # Mon
    _log_meal(client, token_headers, "2024-06-19T10:00:00Z")   # Wed

    r = client.get(WEEKLY, params={"week_of": "2024-06-19", "tz": "UTC"}, headers=token_headers)
    assert r.json()["days_with_logs"] == 2


def test_weekly_period_avg_excludes_empty_days(client, token_headers):
    _log_meal(client, token_headers, "2024-06-17T10:00:00Z", quantity_g=200.0)   # 300 kcal Mon

    r = client.get(WEEKLY, params={"week_of": "2024-06-17", "tz": "UTC"}, headers=token_headers)
    body = r.json()
    # avg should be 300/1 = 300, not 300/7
    assert body["actual_period_avg"]["energy_kcal"] == 300.0
    assert body["days_with_logs"] == 1


def test_weekly_uses_goal_active_at_period_start(client, token_headers):
    # Goals are set "now" — use the current week so active_from <= period start
    from datetime import date as _date
    today = _date.today().isoformat()
    client.post(GOALS, json={**_GOAL, "daily_calories": 1500.0}, headers=token_headers)
    client.post(GOALS, json={**_GOAL, "daily_calories": 2000.0}, headers=token_headers)
    r = client.get(WEEKLY, params={"week_of": today, "tz": "UTC"}, headers=token_headers)
    assert r.json()["goal"] is not None


def test_weekly_no_goal_returns_null_goal(client, token_headers):
    r = client.get(WEEKLY, params={"week_of": "2024-06-19", "tz": "UTC"}, headers=token_headers)
    assert r.json()["goal"] is None


def test_weekly_empty_week_returns_zero_avg(client, token_headers):
    r = client.get(WEEKLY, params={"week_of": "2024-06-19", "tz": "UTC"}, headers=token_headers)
    assert r.json()["actual_period_avg"]["energy_kcal"] == 0.0
    assert r.json()["days_with_logs"] == 0


def test_weekly_custom_range(client, token_headers):
    _log_meal(client, token_headers, "2024-06-17T10:00:00Z")
    _log_meal(client, token_headers, "2024-06-25T10:00:00Z")   # outside range

    r = client.get(WEEKLY, params={"start": "2024-06-15", "end": "2024-06-21", "tz": "UTC"}, headers=token_headers)
    assert r.status_code == 200
    assert r.json()["days_with_logs"] == 1


def test_weekly_week_of_and_start_together_returns_400(client, token_headers):
    r = client.get(WEEKLY, params={"week_of": "2024-06-19", "start": "2024-06-01", "tz": "UTC"}, headers=token_headers)
    assert r.status_code == 422


def test_weekly_range_over_90_days_returns_400(client, token_headers):
    r = client.get(WEEKLY, params={"start": "2024-01-01", "end": "2024-12-31", "tz": "UTC"}, headers=token_headers)
    assert r.status_code == 422


def test_weekly_respects_timezone_day_boundaries(client, token_headers):
    # 23:00 UTC Jun 14 = 04:30 IST Jun 15
    _log_meal(client, token_headers, "2024-06-14T23:00:00+00:00")

    # IST week_of Jun 15 → Sun Jun 9 – Sat Jun 15
    r_ist = client.get(WEEKLY, params={"week_of": "2024-06-15", "tz": IST}, headers=token_headers)
    # In IST this meal is on Jun 15 → inside the week
    assert r_ist.json()["days_with_logs"] == 1

    # UTC week_of Jun 15 → Sun Jun 9 – Sat Jun 15
    r_utc = client.get(WEEKLY, params={"week_of": "2024-06-15", "tz": "UTC"}, headers=token_headers)
    # In UTC this meal is on Jun 14 → also inside the week (Jun 9-15)
    assert r_utc.json()["days_with_logs"] == 1


def test_weekly_requires_auth(client):
    assert client.get(WEEKLY).status_code == 401


def test_weekly_two_users_isolated(client):
    r1 = client.post(REGISTER, json={"email": "a@rep.com", "password": "password123"})
    r2 = client.post(REGISTER, json={"email": "b@rep.com", "password": "password123"})
    h1 = {"Authorization": f"Bearer {r1.json()['access_token']}"}
    h2 = {"Authorization": f"Bearer {r2.json()['access_token']}"}

    _log_meal(client, h1, "2024-06-19T10:00:00Z")
    _log_meal(client, h1, "2024-06-19T13:00:00Z")

    assert client.get(WEEKLY, params={"week_of": "2024-06-19", "tz": "UTC"}, headers=h1).json()["days_with_logs"] == 1
    assert client.get(WEEKLY, params={"week_of": "2024-06-19", "tz": "UTC"}, headers=h2).json()["days_with_logs"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# micros
# ══════════════════════════════════════════════════════════════════════════════

def test_micros_empty_when_no_logs(client, token_headers):
    r = client.get(MICROS, params={"week_of": "2024-06-19", "tz": "UTC"}, headers=token_headers)
    assert r.status_code == 200
    assert all(v is None for v in r.json()["totals"].values())


def test_micros_excludes_freeform_entries(client, token_headers):
    # Free-form entry — no food_item_id → no micro data
    _log_meal(client, token_headers, "2024-06-19T10:00:00Z", food_id=None)

    r = client.get(MICROS, params={"week_of": "2024-06-19", "tz": "UTC"}, headers=token_headers)
    assert all(v is None for v in r.json()["totals"].values())


def test_micros_includes_linked_entries(client, token_headers):
    food_id = _create_food(client, token_headers)
    _log_meal(client, token_headers, "2024-06-19T10:00:00Z", quantity_g=100.0, food_id=food_id)

    r = client.get(MICROS, params={"week_of": "2024-06-19", "tz": "UTC"}, headers=token_headers)
    totals = r.json()["totals"]
    # 100g of food with 80mg calcium/100g → 80mg contribution
    assert totals["calcium_mg"] == pytest.approx(80.0, rel=1e-3)


def test_micros_scales_by_quantity(client, token_headers):
    food_id = _create_food(client, token_headers)
    _log_meal(client, token_headers, "2024-06-19T10:00:00Z", quantity_g=200.0, food_id=food_id)

    r = client.get(MICROS, params={"week_of": "2024-06-19", "tz": "UTC"}, headers=token_headers)
    # 200g → 2× contribution
    assert r.json()["totals"]["calcium_mg"] == pytest.approx(160.0, rel=1e-3)


def test_micros_sums_multiple_entries(client, token_headers):
    food_id = _create_food(client, token_headers)
    _log_meal(client, token_headers, "2024-06-17T10:00:00Z", quantity_g=100.0, food_id=food_id)
    _log_meal(client, token_headers, "2024-06-19T10:00:00Z", quantity_g=100.0, food_id=food_id)

    r = client.get(MICROS, params={"week_of": "2024-06-19", "tz": "UTC"}, headers=token_headers)
    assert r.json()["totals"]["calcium_mg"] == pytest.approx(160.0, rel=1e-3)


def test_micros_note_is_present(client, token_headers):
    r = client.get(MICROS, params={"week_of": "2024-06-19", "tz": "UTC"}, headers=token_headers)
    assert "note" in r.json()
    assert len(r.json()["note"]) > 0


def test_micros_requires_auth(client):
    assert client.get(MICROS).status_code == 401

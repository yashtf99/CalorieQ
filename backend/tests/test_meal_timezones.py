"""
Timezone tests for GET /meals date filtering.

The rule: a meal logged at 2024-06-15T01:00:00+05:30 (IST) is
2024-06-14T19:30:00Z in UTC. It should appear on 2024-06-14 in a UTC
query and on 2024-06-15 in an IST query.
"""

MEALS         = "/api/v1/meals"
MEALS_HISTORY = "/api/v1/meals/history"
REGISTER      = "/api/v1/auth/register"

_BASE = {
    "food_name_snapshot": "Test Food",
    "meal_type": "dinner",
    "quantity_g": 200.0,
    "energy_kcal": 400.0,
    "protein_g": 20.0,
    "carb_g": 50.0,
    "fat_g": 10.0,
}

IST = "Asia/Kolkata"   # UTC+05:30
EST = "America/New_York"  # UTC-05:00 (winter)


def _log(client, headers, logged_at: str):
    return client.post(MEALS, json={**_BASE, "logged_at": logged_at}, headers=headers)


def _count(client, headers, **params):
    r = client.get(MEALS_HISTORY, params=params, headers=headers)
    assert r.status_code == 200, r.json()
    return r.json()["meta"]["total"]


# ── logged_at conversion ──────────────────────────────────────────────────────

def test_logged_at_with_ist_offset_stored_as_utc(client, token_headers):
    """
    A meal at 2024-06-15T01:00:00+05:30 = 2024-06-14T19:30:00Z.
    Querying 2024-06-14 in UTC must find it; 2024-06-15 in UTC must not.
    """
    _log(client, token_headers, "2024-06-15T01:00:00+05:30")

    assert _count(client, token_headers, date="2024-06-14", tz="UTC") == 1
    assert _count(client, token_headers, date="2024-06-15", tz="UTC") == 0


def test_logged_at_with_utc_offset_stored_correctly(client, token_headers):
    """Explicit +00:00 offset must behave identically to a bare UTC datetime."""
    _log(client, token_headers, "2024-06-15T12:00:00+00:00")
    assert _count(client, token_headers, date="2024-06-15", tz="UTC") == 1


def test_logged_at_with_negative_offset(client, token_headers):
    """
    A meal at 2024-06-15T20:00:00-05:00 (EST) = 2024-06-16T01:00:00Z.
    UTC query on 2024-06-15 must not find it; 2024-06-16 must.
    """
    _log(client, token_headers, "2024-06-15T20:00:00-05:00")

    assert _count(client, token_headers, date="2024-06-15", tz="UTC") == 0
    assert _count(client, token_headers, date="2024-06-16", tz="UTC") == 1


# ── query tz param ────────────────────────────────────────────────────────────

def test_ist_day_boundary_shifts_correctly(client, token_headers):
    """
    23:00 IST on Jun 14 = 17:30 UTC Jun 14  → appears on Jun 14 IST, Jun 14 UTC.
    01:00 IST on Jun 15 = 19:30 UTC Jun 14  → appears on Jun 15 IST, Jun 14 UTC.
    """
    _log(client, token_headers, "2024-06-14T23:00:00+05:30")  # 17:30 UTC Jun 14
    _log(client, token_headers, "2024-06-15T01:00:00+05:30")  # 19:30 UTC Jun 14

    # UTC query: both meals are on Jun 14 UTC
    assert _count(client, token_headers, date="2024-06-14", tz="UTC") == 2
    assert _count(client, token_headers, date="2024-06-15", tz="UTC") == 0

    # IST query: first meal is Jun 14 IST, second is Jun 15 IST
    assert _count(client, token_headers, date="2024-06-14", tz=IST) == 1
    assert _count(client, token_headers, date="2024-06-15", tz=IST) == 1


def test_range_with_ist_timezone(client, token_headers):
    """start/end boundaries are resolved in the user's timezone."""
    _log(client, token_headers, "2024-06-15T00:30:00+05:30")  # within Jun 15 IST
    _log(client, token_headers, "2024-06-17T23:59:00+05:30")  # within Jun 17 IST
    _log(client, token_headers, "2024-06-18T00:01:00+05:30")  # Jun 18 IST — outside range

    count = _count(
        client, token_headers,
        start="2024-06-15", end="2024-06-17", tz=IST,
    )
    assert count == 2


def test_same_date_different_tz_returns_different_meals(client, token_headers):
    """
    A meal logged at 2024-06-15T02:00:00+05:30 = 2024-06-14T20:30:00Z.
    - IST query for 2024-06-15: finds it (02:00 IST is on Jun 15 IST).
    - UTC query for 2024-06-15: does not find it (20:30 UTC is on Jun 14 UTC).
    """
    _log(client, token_headers, "2024-06-15T02:00:00+05:30")

    assert _count(client, token_headers, date="2024-06-15", tz=IST) == 1
    assert _count(client, token_headers, date="2024-06-15", tz="UTC") == 0
    assert _count(client, token_headers, date="2024-06-14", tz="UTC") == 1


def test_ist_midnight_exactly_is_start_of_ist_day(client, token_headers):
    """Midnight IST is inclusive — it belongs to that IST day."""
    _log(client, token_headers, "2024-06-15T00:00:00+05:30")
    assert _count(client, token_headers, date="2024-06-15", tz=IST) == 1
    assert _count(client, token_headers, date="2024-06-14", tz=IST) == 0


# ── sub-day precision (HH:MM:SS) ─────────────────────────────────────────────

def test_datetime_range_filters_by_hour(client, token_headers):
    """start/end with HH:MM:SS narrows results to that window."""
    _log(client, token_headers, "2024-06-15T07:59:00+00:00")   # before window
    _log(client, token_headers, "2024-06-15T08:00:00+00:00")   # == start → included
    _log(client, token_headers, "2024-06-15T12:30:00+00:00")   # inside window
    _log(client, token_headers, "2024-06-15T14:00:00+00:00")   # == end → excluded (exclusive)
    _log(client, token_headers, "2024-06-15T14:01:00+00:00")   # after window

    count = _count(
        client, token_headers,
        start="2024-06-15T08:00:00",
        end="2024-06-15T14:00:00",
        tz="UTC",
    )
    assert count == 2  # 08:00 and 12:30


def test_datetime_range_minutes_precision(client, token_headers):
    _log(client, token_headers, "2024-06-15T10:29:59+00:00")   # before
    _log(client, token_headers, "2024-06-15T10:30:00+00:00")   # included
    _log(client, token_headers, "2024-06-15T10:45:00+00:00")   # included
    _log(client, token_headers, "2024-06-15T11:00:00+00:00")   # excluded (== end)

    count = _count(
        client, token_headers,
        start="2024-06-15T10:30:00",
        end="2024-06-15T11:00:00",
        tz="UTC",
    )
    assert count == 2


def test_datetime_start_end_with_ist_offset(client, token_headers):
    """HH:MM:SS bounds in IST convert to UTC correctly."""
    # 09:00 IST = 03:30 UTC, 17:00 IST = 11:30 UTC
    _log(client, token_headers, "2024-06-15T03:29:00+00:00")   # before 09:00 IST
    _log(client, token_headers, "2024-06-15T03:30:00+00:00")   # == 09:00 IST → included
    _log(client, token_headers, "2024-06-15T08:00:00+00:00")   # inside
    _log(client, token_headers, "2024-06-15T11:30:00+00:00")   # == 17:00 IST → excluded
    _log(client, token_headers, "2024-06-15T11:31:00+00:00")   # after

    count = _count(
        client, token_headers,
        start="2024-06-15T09:00:00",
        end="2024-06-15T17:00:00",
        tz=IST,
    )
    assert count == 2  # 03:30 UTC and 08:00 UTC


def test_mixed_date_and_datetime_bounds(client, token_headers):
    """start as date, end as datetime."""
    _log(client, token_headers, "2024-06-15T00:00:00+00:00")  # included
    _log(client, token_headers, "2024-06-15T11:59:59+00:00")  # included
    _log(client, token_headers, "2024-06-15T12:00:00+00:00")  # excluded (== end)

    count = _count(
        client, token_headers,
        start="2024-06-15",
        end="2024-06-15T12:00:00",
        tz="UTC",
    )
    assert count == 2


def test_end_before_start_datetime_returns_400(client, token_headers):
    r = client.get(MEALS_HISTORY, params={
        "start": "2024-06-15T14:00:00",
        "end": "2024-06-15T08:00:00",
        "tz": "UTC",
    }, headers=token_headers)
    assert r.status_code == 422


def test_two_users_timezone_filtering_is_isolated(client):
    r1 = client.post(REGISTER, json={"email": "a@tz.com", "password": "password123"})
    r2 = client.post(REGISTER, json={"email": "b@tz.com", "password": "password123"})
    h1 = {"Authorization": f"Bearer {r1.json()['access_token']}"}
    h2 = {"Authorization": f"Bearer {r2.json()['access_token']}"}

    _log(client, h1, "2024-06-15T10:00:00+05:30")
    _log(client, h2, "2024-06-15T10:00:00+05:30")

    assert _count(client, h1, date="2024-06-15", tz=IST) == 1
    assert _count(client, h2, date="2024-06-15", tz=IST) == 1

    # User 2 logs a second meal — should not affect user 1's count
    _log(client, h2, "2024-06-15T14:00:00+05:30")
    assert _count(client, h1, date="2024-06-15", tz=IST) == 1
    assert _count(client, h2, date="2024-06-15", tz=IST) == 2

"""
Regression tests for bugs found during critique.
Each test documents the exact broken flow and asserts the correct behaviour.
"""

REGISTER = "/api/v1/auth/register"
LOGIN    = "/api/v1/auth/login"
PROFILE  = "/api/v1/users/me/profile"
GOALS    = "/api/v1/goals"

_BASE_USER = {"email": "bug@test.com", "password": "password123"}


# ── Bug 1: bcrypt 72-byte truncation ─────────────────────────────────────────
# Passwords longer than 72 bytes used to be silently truncated by bcrypt,
# meaning login with just the first 72 chars would succeed.

def test_password_longer_than_72_bytes_is_not_truncated(client):
    long_password   = "a" * 73
    short_password  = "a" * 72   # same first 72 bytes

    client.post(REGISTER, json={"email": "bug@test.com", "password": long_password})

    r = client.post(LOGIN, json={"email": "bug@test.com", "password": short_password})
    assert r.status_code == 401, "72-char prefix of a longer password must not authenticate"


def test_long_password_still_works_with_correct_value(client):
    long_password = "a" * 100
    client.post(REGISTER, json={"email": "bug@test.com", "password": long_password})
    r = client.post(LOGIN, json={"email": "bug@test.com", "password": long_password})
    assert r.status_code == 200


# ── Bug 2: concurrent register race → 500 ────────────────────────────────────
# Duplicate email must always return 409, never 500, even when the pre-commit
# uniqueness check is bypassed (simulated here by calling register twice quickly).

def test_duplicate_register_always_409_not_500(client):
    client.post(REGISTER, json=_BASE_USER)
    r = client.post(REGISTER, json=_BASE_USER)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "CONFLICT"


# ── Bug 4: GET /profile before setup returns shifting updated_at ─────────────
# Before any profile is saved, updated_at used to be datetime.now() on every
# call — meaning two identical GETs returned different values.

def test_profile_before_setup_has_stable_null_updated_at(client, token_headers):
    r1 = client.get(PROFILE, headers=token_headers)
    r2 = client.get(PROFILE, headers=token_headers)
    assert r1.json()["updated_at"] is None
    assert r1.json()["updated_at"] == r2.json()["updated_at"]


# ── Bug 5: PATCH /profile {} creates a spurious DB write ─────────────────────
# An empty PATCH body used to create a profile row with all nulls and bump
# updated_at — even though nothing changed.

def test_patch_profile_empty_body_does_not_create_profile_row(client, token_headers):
    client.patch(PROFILE, json={}, headers=token_headers)
    r = client.get(PROFILE, headers=token_headers)
    # Profile row was never written — updated_at must still be None
    assert r.json()["updated_at"] is None


def test_patch_profile_empty_body_after_real_patch_does_not_bump_updated_at(client, token_headers):
    client.patch(PROFILE, json={"height_cm": 175.0}, headers=token_headers)
    ts1 = client.get(PROFILE, headers=token_headers).json()["updated_at"]

    client.patch(PROFILE, json={}, headers=token_headers)  # no-op
    ts2 = client.get(PROFILE, headers=token_headers).json()["updated_at"]

    assert ts1 == ts2, "updated_at must not change on a no-op PATCH"


# ── Bug 6: Numeric overflow → 500 instead of 400 ────────────────────────────
# Numeric(7,2) max is 99999.99; values above that used to hit the DB and 500.

def test_goal_calories_above_numeric_limit_returns_400(client, token_headers):
    r = client.post(GOALS, json={"goal_type": "lose", "daily_calories": 100_000}, headers=token_headers)
    assert r.status_code == 400


def test_goal_protein_above_limit_returns_400(client, token_headers):
    r = client.post(GOALS, json={"goal_type": "lose", "protein_g": 100_000}, headers=token_headers)
    assert r.status_code == 400

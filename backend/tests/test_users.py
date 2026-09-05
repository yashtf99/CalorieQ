ME       = "/api/v1/users/me"
PROFILE  = "/api/v1/users/me/profile"
REGISTER = "/api/v1/auth/register"


# ── GET /users/me ─────────────────────────────────────────────────────────────

def test_get_me_returns_user(client, token_headers):
    r = client.get(ME, headers=token_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "fixture@test.com"
    assert body["display_name"] == "Fixture User"
    assert "id" in body
    assert "password_hash" not in body


def test_get_me_requires_auth(client):
    r = client.get(ME)
    assert r.status_code == 401


def test_get_me_invalid_token_returns_401(client):
    r = client.get(ME, headers={"Authorization": "Bearer garbage"})
    assert r.status_code == 401


# ── PATCH /users/me ───────────────────────────────────────────────────────────

def test_patch_me_updates_display_name(client, token_headers):
    r = client.patch(ME, json={"display_name": "New Name"}, headers=token_headers)
    assert r.status_code == 200
    assert r.json()["display_name"] == "New Name"


def test_patch_me_empty_display_name_returns_400(client, token_headers):
    r = client.patch(ME, json={"display_name": ""}, headers=token_headers)
    assert r.status_code == 400


def test_patch_me_null_display_name_is_allowed(client, token_headers):
    r = client.patch(ME, json={"display_name": None}, headers=token_headers)
    assert r.status_code == 200


def test_patch_me_requires_auth(client):
    r = client.patch(ME, json={"display_name": "X"})
    assert r.status_code == 401


# ── GET /users/me/profile ─────────────────────────────────────────────────────

def test_get_profile_before_setup_returns_nulls(client, token_headers):
    r = client.get(PROFILE, headers=token_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["height_cm"] is None
    assert body["gender"] is None
    assert body["current_weight_kg"] is None


def test_get_profile_requires_auth(client):
    r = client.get(PROFILE)
    assert r.status_code == 401


# ── PATCH /users/me/profile ───────────────────────────────────────────────────

def test_patch_profile_sets_physical_stats(client, token_headers):
    r = client.patch(PROFILE, json={
        "dob": "1995-06-15",
        "gender": "male",
        "height_cm": 175.5,
        "activity_level": "lightly_active",
    }, headers=token_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["height_cm"] == 175.5
    assert body["gender"] == "male"
    assert body["activity_level"] == "lightly_active"
    assert body["dob"] == "1995-06-15"


def test_patch_profile_with_current_weight_logs_weight_entry(client, token_headers):
    r = client.patch(PROFILE, json={"current_weight_kg": 78.5}, headers=token_headers)
    assert r.status_code == 200
    assert r.json()["current_weight_kg"] == 78.5


def test_patch_profile_weight_shows_in_get(client, token_headers):
    client.patch(PROFILE, json={"current_weight_kg": 80.0}, headers=token_headers)
    r = client.get(PROFILE, headers=token_headers)
    assert r.status_code == 200
    assert r.json()["current_weight_kg"] == 80.0


def test_patch_profile_multiple_weight_entries_returns_latest(client, token_headers):
    client.patch(PROFILE, json={"current_weight_kg": 80.0}, headers=token_headers)
    client.patch(PROFILE, json={"current_weight_kg": 79.2}, headers=token_headers)
    r = client.get(PROFILE, headers=token_headers)
    assert r.json()["current_weight_kg"] == 79.2


def test_patch_profile_is_partial(client, token_headers):
    client.patch(PROFILE, json={"height_cm": 175.0}, headers=token_headers)
    client.patch(PROFILE, json={"gender": "male"}, headers=token_headers)
    r = client.get(PROFILE, headers=token_headers)
    body = r.json()
    assert body["height_cm"] == 175.0  # still set from first patch
    assert body["gender"] == "male"


def test_patch_profile_invalid_height_returns_400(client, token_headers):
    r = client.patch(PROFILE, json={"height_cm": 5.0}, headers=token_headers)  # < 50 cm
    assert r.status_code == 400


def test_patch_profile_invalid_weight_returns_400(client, token_headers):
    r = client.patch(PROFILE, json={"current_weight_kg": 5.0}, headers=token_headers)  # < 20 kg
    assert r.status_code == 400


def test_patch_profile_invalid_gender_returns_400(client, token_headers):
    r = client.patch(PROFILE, json={"gender": "attack_helicopter"}, headers=token_headers)
    assert r.status_code == 400


def test_patch_profile_two_users_isolated(client):
    """Two users' profiles must not bleed into each other."""
    r1 = client.post(REGISTER, json={"email": "a@test.com", "password": "password123"})
    r2 = client.post(REGISTER, json={"email": "b@test.com", "password": "password123"})
    h1 = {"Authorization": f"Bearer {r1.json()['access_token']}"}
    h2 = {"Authorization": f"Bearer {r2.json()['access_token']}"}

    client.patch(PROFILE, json={"height_cm": 160.0}, headers=h1)
    client.patch(PROFILE, json={"height_cm": 190.0}, headers=h2)

    assert client.get(PROFILE, headers=h1).json()["height_cm"] == 160.0
    assert client.get(PROFILE, headers=h2).json()["height_cm"] == 190.0

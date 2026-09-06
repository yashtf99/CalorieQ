GOALS         = "/api/v1/goals"
GOALS_ACTIVE  = "/api/v1/goals/active"
GOALS_HISTORY = "/api/v1/goals/history"
GOALS_SUGGEST = "/api/v1/goals/suggest"
REGISTER      = "/api/v1/auth/register"

_SUGGEST_PARAMS = {
    "height_cm":      175.0,
    "weight_kg":      75.0,
    "dob":            "1995-06-15",
    "gender":         "male",
    "activity_level": "lightly_active",
}

_GOAL = {
    "goal_type": "lose",
    "daily_calories": 1800.0,
    "protein_g": 140.0,
    "carbs_g": 180.0,
    "fat_g": 55.0,
    "fibre_g": 30.0,
    "weight_target_kg": 72.0,
}


# ── GET /goals/suggest ───────────────────────────────────────────────────────

def test_suggest_returns_bmr_tdee_and_three_goal_types(client, token_headers):
    r = client.get(GOALS_SUGGEST, params=_SUGGEST_PARAMS, headers=token_headers)
    assert r.status_code == 200
    body = r.json()
    assert "bmr" in body and body["bmr"] > 0
    assert "tdee" in body and body["tdee"] >= body["bmr"]
    assert set(body["suggestions"].keys()) == {"lose", "maintain", "gain"}


def test_suggest_lose_calories_less_than_maintain(client, token_headers):
    r = client.get(GOALS_SUGGEST, params=_SUGGEST_PARAMS, headers=token_headers).json()
    assert r["suggestions"]["lose"]["daily_calories"] < r["suggestions"]["maintain"]["daily_calories"]


def test_suggest_gain_calories_more_than_maintain(client, token_headers):
    r = client.get(GOALS_SUGGEST, params=_SUGGEST_PARAMS, headers=token_headers).json()
    assert r["suggestions"]["gain"]["daily_calories"] > r["suggestions"]["maintain"]["daily_calories"]


def test_suggest_each_suggestion_has_all_macro_fields(client, token_headers):
    r = client.get(GOALS_SUGGEST, params=_SUGGEST_PARAMS, headers=token_headers).json()
    for goal_type in ("lose", "maintain", "gain"):
        s = r["suggestions"][goal_type]
        for field in ("daily_calories", "protein_g", "carbs_g", "fat_g", "fibre_g"):
            assert field in s and s[field] > 0


def test_suggest_requires_auth(client):
    r = client.get(GOALS_SUGGEST, params=_SUGGEST_PARAMS)
    assert r.status_code == 401


def test_suggest_rejects_future_dob(client, token_headers):
    r = client.get(GOALS_SUGGEST, params={**_SUGGEST_PARAMS, "dob": "2099-01-01"}, headers=token_headers)
    assert r.status_code == 422


def test_suggest_rejects_invalid_activity_level(client, token_headers):
    r = client.get(GOALS_SUGGEST, params={**_SUGGEST_PARAMS, "activity_level": "superhuman"}, headers=token_headers)
    assert r.status_code == 400


def test_suggest_rejects_out_of_range_weight(client, token_headers):
    r = client.get(GOALS_SUGGEST, params={**_SUGGEST_PARAMS, "weight_kg": 600}, headers=token_headers)
    assert r.status_code == 400


def test_suggest_lose_never_below_1200_kcal(client, token_headers):
    # Very small/light person — lose suggestion should still be >= 1200
    params = {**_SUGGEST_PARAMS, "weight_kg": 21, "height_cm": 51, "activity_level": "sedentary"}
    r = client.get(GOALS_SUGGEST, params=params, headers=token_headers).json()
    assert r["suggestions"]["lose"]["daily_calories"] >= 1200


# ── POST /goals ───────────────────────────────────────────────────────────────

def test_create_goal_returns_201(client, token_headers):
    r = client.post(GOALS, json=_GOAL, headers=token_headers)
    assert r.status_code == 201
    body = r.json()
    assert body["goal_type"] == "lose"
    assert body["daily_calories"] == 1800.0
    assert body["weight_target_kg"] == 72.0
    assert body["active_to"] is None
    assert "id" in body
    assert "active_from" in body


def test_create_goal_requires_auth(client):
    r = client.post(GOALS, json=_GOAL)
    assert r.status_code == 401


def test_create_goal_requires_goal_type(client, token_headers):
    r = client.post(GOALS, json={**_GOAL, "goal_type": None}, headers=token_headers)
    assert r.status_code == 400


def test_create_goal_rejects_invalid_goal_type(client, token_headers):
    r = client.post(GOALS, json={**_GOAL, "goal_type": "bulk"}, headers=token_headers)
    assert r.status_code == 400


def test_create_goal_rejects_negative_calories(client, token_headers):
    r = client.post(GOALS, json={**_GOAL, "daily_calories": -100}, headers=token_headers)
    assert r.status_code == 400


def test_create_goal_rejects_negative_macros(client, token_headers):
    r = client.post(GOALS, json={**_GOAL, "protein_g": -10}, headers=token_headers)
    assert r.status_code == 400


def test_create_goal_all_nutrient_fields_optional(client, token_headers):
    r = client.post(GOALS, json={"goal_type": "maintain"}, headers=token_headers)
    assert r.status_code == 201
    body = r.json()
    assert body["daily_calories"] is None
    assert body["weight_target_kg"] is None


def test_create_goal_closes_previous_active_goal(client, token_headers):
    first = client.post(GOALS, json=_GOAL, headers=token_headers).json()
    assert first["active_to"] is None

    client.post(GOALS, json={**_GOAL, "goal_type": "maintain"}, headers=token_headers)

    # First goal must now be closed
    history = client.get(GOALS_HISTORY, headers=token_headers).json()["data"]
    first_in_history = next(g for g in history if g["id"] == first["id"])
    assert first_in_history["active_to"] is not None


def test_create_goal_only_one_active_at_a_time(client, token_headers):
    client.post(GOALS, json=_GOAL, headers=token_headers)
    client.post(GOALS, json={**_GOAL, "goal_type": "maintain"}, headers=token_headers)
    client.post(GOALS, json={**_GOAL, "goal_type": "gain"}, headers=token_headers)

    active = client.get(GOALS_ACTIVE, headers=token_headers).json()
    assert active["goal_type"] == "gain"


# ── GET /goals/active ─────────────────────────────────────────────────────────

def test_get_active_goal_returns_latest(client, token_headers):
    client.post(GOALS, json=_GOAL, headers=token_headers)
    r = client.get(GOALS_ACTIVE, headers=token_headers)
    assert r.status_code == 200
    assert r.json()["goal_type"] == "lose"
    assert r.json()["active_to"] is None


def test_get_active_goal_404_when_no_goal_set(client, token_headers):
    r = client.get(GOALS_ACTIVE, headers=token_headers)
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"


def test_get_active_goal_requires_auth(client):
    r = client.get(GOALS_ACTIVE)
    assert r.status_code == 401


# ── GET /goals/history ────────────────────────────────────────────────────────

def test_goals_history_empty_when_no_goals(client, token_headers):
    r = client.get(GOALS_HISTORY, headers=token_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["data"] == []
    assert body["meta"]["total"] == 0


def test_goals_history_returns_all_goals(client, token_headers):
    client.post(GOALS, json=_GOAL, headers=token_headers)
    client.post(GOALS, json={**_GOAL, "goal_type": "maintain"}, headers=token_headers)
    r = client.get(GOALS_HISTORY, headers=token_headers)
    body = r.json()
    assert body["meta"]["total"] == 2
    assert len(body["data"]) == 2


def test_goals_history_newest_first(client, token_headers):
    client.post(GOALS, json=_GOAL, headers=token_headers)
    client.post(GOALS, json={**_GOAL, "goal_type": "gain"}, headers=token_headers)
    history = client.get(GOALS_HISTORY, headers=token_headers).json()["data"]
    assert history[0]["goal_type"] == "gain"


def test_goals_history_pagination(client, token_headers):
    for i in range(5):
        client.post(GOALS, json={**_GOAL, "goal_type": "maintain"}, headers=token_headers)

    page1 = client.get(GOALS_HISTORY, params={"page": 1, "page_size": 3}, headers=token_headers).json()
    page2 = client.get(GOALS_HISTORY, params={"page": 2, "page_size": 3}, headers=token_headers).json()

    assert len(page1["data"]) == 3
    assert len(page2["data"]) == 2
    assert page1["meta"]["total_pages"] == 2
    assert page1["meta"]["total"] == 5


def test_goals_history_requires_auth(client):
    r = client.get(GOALS_HISTORY)
    assert r.status_code == 401


def test_goals_two_users_isolated(client):
    """Goals for user A must not appear in user B's history."""
    r1 = client.post(REGISTER, json={"email": "a@test.com", "password": "password123"})
    r2 = client.post(REGISTER, json={"email": "b@test.com", "password": "password123"})
    h1 = {"Authorization": f"Bearer {r1.json()['access_token']}"}
    h2 = {"Authorization": f"Bearer {r2.json()['access_token']}"}

    client.post(GOALS, json=_GOAL, headers=h1)
    client.post(GOALS, json=_GOAL, headers=h1)

    assert client.get(GOALS_HISTORY, headers=h2).json()["meta"]["total"] == 0
    assert client.get(GOALS_ACTIVE, headers=h2).status_code == 404

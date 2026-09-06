GOALS         = "/api/v1/goals"
GOALS_ACTIVE  = "/api/v1/goals/active"
GOALS_HISTORY = "/api/v1/goals/history"
REGISTER      = "/api/v1/auth/register"

_GOAL = {
    "goal_type": "lose",
    "daily_calories": 1800.0,
    "protein_g": 140.0,
    "carbs_g": 180.0,
    "fat_g": 55.0,
    "fibre_g": 30.0,
    "weight_target_kg": 72.0,
}


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

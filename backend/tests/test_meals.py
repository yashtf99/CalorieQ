"""
Meal entry tests — covers food item search/CRUD and meal log CRUD.
Each test uses a fresh in-memory DB via conftest fixtures.
"""
import uuid

import pytest

REGISTER     = "/api/v1/auth/register"
FOOD_ITEMS   = "/api/v1/food_items"
MEALS        = "/api/v1/meals"

_FOOD = {
    "name": "Dal Makhani",
    "category": "Legumes",
    "energy_kcal": 131.0,   # per 100g
    "protein_g": 6.2,
    "carb_g": 15.3,
    "fat_g": 5.1,
    "fibre_g": 3.8,
    "sodium_mg": 210.0,
}

_LINKED_MEAL = {
    "meal_type": "lunch",
    "quantity_g": 200.0,
}

_FREE_MEAL = {
    "food_name_snapshot": "Restaurant Biryani",
    "meal_type": "dinner",
    "quantity_g": 400.0,
    "energy_kcal": 520.0,
    "protein_g": 18.0,
    "carb_g": 72.0,
    "fat_g": 16.0,
    "source": "user",
}


# ── helpers ───────────────────────────────────────────────────────────────────

def _create_food(client, headers, payload=None):
    return client.post(FOOD_ITEMS, json=payload or _FOOD, headers=headers)


def _second_user(client):
    r = client.post(REGISTER, json={"email": "b@test.com", "password": "password123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


# ══════════════════════════════════════════════════════════════════════════════
# Food item search
# ══════════════════════════════════════════════════════════════════════════════

def test_food_search_empty_db_returns_empty(client, token_headers):
    r = client.get(FOOD_ITEMS, params={"q": "chicken"}, headers=token_headers)
    assert r.status_code == 200
    assert r.json()["data"] == []
    assert r.json()["meta"]["total"] == 0


def test_food_search_requires_auth(client):
    r = client.get(FOOD_ITEMS, params={"q": "dal"})
    assert r.status_code == 401


def test_food_search_finds_by_name(client, token_headers):
    _create_food(client, token_headers)
    r = client.get(FOOD_ITEMS, params={"q": "dal"}, headers=token_headers)
    assert r.status_code == 200
    assert r.json()["meta"]["total"] == 1
    assert r.json()["data"][0]["name"] == "Dal Makhani"


def test_food_search_case_insensitive(client, token_headers):
    _create_food(client, token_headers)
    r = client.get(FOOD_ITEMS, params={"q": "DAL MAKHANI"}, headers=token_headers)
    assert r.json()["meta"]["total"] == 1


def test_food_search_partial_match(client, token_headers):
    _create_food(client, token_headers)
    r = client.get(FOOD_ITEMS, params={"q": "makh"}, headers=token_headers)
    assert r.json()["meta"]["total"] == 1


def test_food_search_no_match_returns_empty(client, token_headers):
    _create_food(client, token_headers)
    r = client.get(FOOD_ITEMS, params={"q": "pizza"}, headers=token_headers)
    assert r.json()["meta"]["total"] == 0


def test_food_search_page_size_capped_at_20(client, token_headers):
    r = client.get(FOOD_ITEMS, params={"q": "x", "page_size": 50}, headers=token_headers)
    assert r.status_code == 400


# ══════════════════════════════════════════════════════════════════════════════
# Food item detail
# ══════════════════════════════════════════════════════════════════════════════

def test_get_food_item_detail(client, token_headers):
    food_id = _create_food(client, token_headers).json()["id"]
    r = client.get(f"{FOOD_ITEMS}/{food_id}", headers=token_headers)
    assert r.status_code == 200
    assert r.json()["id"] == food_id
    assert "portions" in r.json()


def test_get_food_item_not_found(client, token_headers):
    r = client.get(f"{FOOD_ITEMS}/{uuid.uuid4()}", headers=token_headers)
    assert r.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# Custom food CRUD
# ══════════════════════════════════════════════════════════════════════════════

def test_create_custom_food_returns_201(client, token_headers):
    r = _create_food(client, token_headers)
    assert r.status_code == 201
    assert r.json()["source"] == "user_custom"
    assert r.json()["is_verified"] is False


def test_create_custom_food_requires_name_and_kcal(client, token_headers):
    r = client.post(FOOD_ITEMS, json={"name": "Test"}, headers=token_headers)
    assert r.status_code == 400


def test_update_own_custom_food(client, token_headers):
    food_id = _create_food(client, token_headers).json()["id"]
    r = client.patch(f"{FOOD_ITEMS}/{food_id}", json={**_FOOD, "name": "Updated Dal"}, headers=token_headers)
    assert r.status_code == 200
    assert r.json()["name"] == "Updated Dal"


def test_update_other_users_custom_food_forbidden(client, token_headers):
    food_id = _create_food(client, token_headers).json()["id"]
    h2 = _second_user(client)
    r = client.patch(f"{FOOD_ITEMS}/{food_id}", json=_FOOD, headers=h2)
    assert r.status_code == 403


def test_delete_own_custom_food(client, token_headers):
    food_id = _create_food(client, token_headers).json()["id"]
    r = client.delete(f"{FOOD_ITEMS}/{food_id}", headers=token_headers)
    assert r.status_code == 204


def test_delete_other_users_custom_food_forbidden(client, token_headers):
    food_id = _create_food(client, token_headers).json()["id"]
    h2 = _second_user(client)
    r = client.delete(f"{FOOD_ITEMS}/{food_id}", headers=h2)
    assert r.status_code == 403


def test_delete_food_referenced_by_meal_log_returns_409(client, token_headers):
    food_id = _create_food(client, token_headers).json()["id"]
    client.post(MEALS, json={**_LINKED_MEAL, "food_item_id": food_id}, headers=token_headers)
    r = client.delete(f"{FOOD_ITEMS}/{food_id}", headers=token_headers)
    assert r.status_code == 409


# ══════════════════════════════════════════════════════════════════════════════
# Meal log — POST (linked entry)
# ══════════════════════════════════════════════════════════════════════════════

def test_create_linked_meal_scales_macros(client, token_headers):
    food_id = _create_food(client, token_headers).json()["id"]
    r = client.post(MEALS, json={**_LINKED_MEAL, "food_item_id": food_id}, headers=token_headers)
    assert r.status_code == 201
    body = r.json()
    # 200g of dal makhani (131 kcal/100g) → 262 kcal
    assert abs(body["energy_kcal"] - 262.0) < 0.1
    assert body["food_item_id"] == food_id
    assert body["food_name_snapshot"] == "Dal Makhani"
    assert body["meal_type"] == "lunch"
    assert body["source"] == "user"


def test_create_linked_meal_unknown_food_404(client, token_headers):
    r = client.post(MEALS, json={**_LINKED_MEAL, "food_item_id": str(uuid.uuid4())}, headers=token_headers)
    assert r.status_code == 404


def test_create_linked_meal_other_users_custom_food_forbidden(client, token_headers):
    food_id = _create_food(client, token_headers).json()["id"]
    h2 = _second_user(client)
    r = client.post(MEALS, json={**_LINKED_MEAL, "food_item_id": food_id}, headers=h2)
    assert r.status_code == 403


# ══════════════════════════════════════════════════════════════════════════════
# Meal log — POST (free-form entry)
# ══════════════════════════════════════════════════════════════════════════════

def test_create_freeform_meal_success(client, token_headers):
    r = client.post(MEALS, json=_FREE_MEAL, headers=token_headers)
    assert r.status_code == 201
    body = r.json()
    assert body["food_item_id"] is None
    assert body["energy_kcal"] == 520.0
    assert body["food_name_snapshot"] == "Restaurant Biryani"


def test_create_meal_missing_food_item_id_and_snapshot_returns_400(client, token_headers):
    r = client.post(MEALS, json={"meal_type": "lunch", "quantity_g": 200.0}, headers=token_headers)
    assert r.status_code == 400


def test_create_meal_both_food_item_id_and_snapshot_returns_400(client, token_headers):
    food_id = _create_food(client, token_headers).json()["id"]
    r = client.post(MEALS, json={
        **_FREE_MEAL,
        "food_item_id": food_id,
    }, headers=token_headers)
    assert r.status_code == 400


def test_create_freeform_meal_missing_kcal_returns_400(client, token_headers):
    r = client.post(MEALS, json={
        "food_name_snapshot": "Mystery Food",
        "meal_type": "lunch",
        "quantity_g": 100.0,
    }, headers=token_headers)
    assert r.status_code == 400


# ══════════════════════════════════════════════════════════════════════════════
# Validation — caps
# ══════════════════════════════════════════════════════════════════════════════

def test_quantity_above_cap_returns_400(client, token_headers):
    r = client.post(MEALS, json={**_FREE_MEAL, "quantity_g": 5000.0}, headers=token_headers)
    assert r.status_code == 400


def test_quantity_zero_returns_400(client, token_headers):
    r = client.post(MEALS, json={**_FREE_MEAL, "quantity_g": 0.0}, headers=token_headers)
    assert r.status_code == 400


def test_energy_above_cap_returns_400(client, token_headers):
    r = client.post(MEALS, json={**_FREE_MEAL, "energy_kcal": 11000.0}, headers=token_headers)
    assert r.status_code == 400


def test_invalid_meal_type_returns_400(client, token_headers):
    r = client.post(MEALS, json={**_FREE_MEAL, "meal_type": "midnight_snack"}, headers=token_headers)
    assert r.status_code == 400


# ══════════════════════════════════════════════════════════════════════════════
# Meal log — GET list
# ══════════════════════════════════════════════════════════════════════════════

def test_list_meals_defaults_to_today(client, token_headers):
    client.post(MEALS, json=_FREE_MEAL, headers=token_headers)
    r = client.get(MEALS, headers=token_headers)
    assert r.status_code == 200
    assert r.json()["meta"]["total"] == 1


def test_list_meals_with_date_filter(client, token_headers):
    # Use a fixed past date so the test is timezone-agnostic
    meal = {**_FREE_MEAL, "logged_at": "2024-06-15T12:00:00Z"}
    client.post(MEALS, json=meal, headers=token_headers)
    r = client.get(MEALS, params={"date": "2024-06-15", "tz": "UTC"}, headers=token_headers)
    assert r.status_code == 200
    assert r.json()["meta"]["total"] == 1


def test_list_meals_date_and_range_together_returns_400(client, token_headers):
    r = client.get(MEALS, params={
        "date": "2024-01-15",
        "start": "2024-01-01",
        "tz": "UTC",
    }, headers=token_headers)
    assert r.status_code == 422


def test_list_meals_start_without_end_returns_400(client, token_headers):
    r = client.get(MEALS, params={"start": "2024-01-01", "tz": "UTC"}, headers=token_headers)
    assert r.status_code == 422


def test_list_meals_end_before_start_returns_400(client, token_headers):
    r = client.get(MEALS, params={
        "start": "2024-01-15",
        "end": "2024-01-01",
        "tz": "UTC",
    }, headers=token_headers)
    assert r.status_code == 422


def test_list_meals_invalid_timezone_returns_400(client, token_headers):
    r = client.get(MEALS, params={"tz": "Mars/Olympus"}, headers=token_headers)
    assert r.status_code == 422


def test_list_meals_meal_type_filter(client, token_headers):
    client.post(MEALS, json=_FREE_MEAL, headers=token_headers)  # dinner
    client.post(MEALS, json={**_FREE_MEAL, "meal_type": "breakfast"}, headers=token_headers)
    r = client.get(MEALS, params={"meal_type": "breakfast"}, headers=token_headers)
    assert r.json()["meta"]["total"] == 1
    assert r.json()["data"][0]["meal_type"] == "breakfast"


def test_list_meals_two_users_isolated(client, token_headers):
    client.post(MEALS, json=_FREE_MEAL, headers=token_headers)
    h2 = _second_user(client)
    r = client.get(MEALS, headers=h2)
    assert r.json()["meta"]["total"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# Meal log — GET single / PATCH / DELETE
# ══════════════════════════════════════════════════════════════════════════════

def test_get_meal_log_by_id(client, token_headers):
    log_id = client.post(MEALS, json=_FREE_MEAL, headers=token_headers).json()["id"]
    r = client.get(f"{MEALS}/{log_id}", headers=token_headers)
    assert r.status_code == 200
    assert r.json()["id"] == log_id


def test_get_meal_log_other_user_forbidden(client, token_headers):
    log_id = client.post(MEALS, json=_FREE_MEAL, headers=token_headers).json()["id"]
    h2 = _second_user(client)
    r = client.get(f"{MEALS}/{log_id}", headers=h2)
    assert r.status_code == 403


def test_patch_linked_meal_recalculates_macros(client, token_headers):
    food_id = _create_food(client, token_headers).json()["id"]
    log_id = client.post(MEALS, json={**_LINKED_MEAL, "food_item_id": food_id}, headers=token_headers).json()["id"]
    r = client.patch(f"{MEALS}/{log_id}", json={"quantity_g": 100.0}, headers=token_headers)
    assert r.status_code == 200
    assert abs(r.json()["energy_kcal"] - 131.0) < 0.1  # 100g → 131 kcal


def test_patch_freeform_meal_overrides_nutrition(client, token_headers):
    log_id = client.post(MEALS, json=_FREE_MEAL, headers=token_headers).json()["id"]
    r = client.patch(f"{MEALS}/{log_id}", json={"energy_kcal": 300.0}, headers=token_headers)
    assert r.status_code == 200
    assert r.json()["energy_kcal"] == 300.0


def test_patch_linked_meal_nutrition_fields_ignored(client, token_headers):
    """Passing nutrition fields directly on a linked entry should be ignored — macros come from food item."""
    food_id = _create_food(client, token_headers).json()["id"]
    log_id = client.post(MEALS, json={**_LINKED_MEAL, "food_item_id": food_id}, headers=token_headers).json()["id"]
    r = client.patch(f"{MEALS}/{log_id}", json={"energy_kcal": 9999.0}, headers=token_headers)
    assert r.status_code == 200
    assert r.json()["energy_kcal"] != 9999.0  # ignored


def test_patch_meal_other_user_forbidden(client, token_headers):
    log_id = client.post(MEALS, json=_FREE_MEAL, headers=token_headers).json()["id"]
    h2 = _second_user(client)
    r = client.patch(f"{MEALS}/{log_id}", json={"meal_type": "breakfast"}, headers=h2)
    assert r.status_code == 403


def test_delete_meal_log(client, token_headers):
    log_id = client.post(MEALS, json=_FREE_MEAL, headers=token_headers).json()["id"]
    r = client.delete(f"{MEALS}/{log_id}", headers=token_headers)
    assert r.status_code == 204
    assert client.get(f"{MEALS}/{log_id}", headers=token_headers).status_code == 404


def test_delete_meal_other_user_forbidden(client, token_headers):
    log_id = client.post(MEALS, json=_FREE_MEAL, headers=token_headers).json()["id"]
    h2 = _second_user(client)
    r = client.delete(f"{MEALS}/{log_id}", headers=h2)
    assert r.status_code == 403

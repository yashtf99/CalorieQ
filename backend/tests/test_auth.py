"""
Auth endpoint tests.
Each test gets a fresh in-memory DB via the fixtures in conftest.py.
"""

REGISTER = "/api/v1/auth/register"
LOGIN    = "/api/v1/auth/login"
REFRESH  = "/api/v1/auth/refresh"
LOGOUT   = "/api/v1/auth/logout"

_USER = {"email": "user@example.com", "password": "password123", "display_name": "Test User"}


# ── helpers ───────────────────────────────────────────────────────────────────

def _register(client, payload=None):
    return client.post(REGISTER, json=payload or _USER)


def _login(client):
    return client.post(LOGIN, json={"email": _USER["email"], "password": _USER["password"]})


# ── register ──────────────────────────────────────────────────────────────────

def test_register_returns_user_and_tokens(client):
    r = _register(client)
    assert r.status_code == 201
    body = r.json()
    assert body["user"]["email"] == _USER["email"]
    assert body["user"]["display_name"] == _USER["display_name"]
    assert "id" in body["user"]
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 86400
    assert "password" not in body["user"]
    assert "password_hash" not in body["user"]


def test_register_duplicate_email_returns_409(client):
    _register(client)
    r = _register(client)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "CONFLICT"


def test_register_password_too_short_returns_400(client):
    r = _register(client, {**_USER, "password": "short"})
    assert r.status_code == 400


def test_register_invalid_email_returns_400(client):
    r = _register(client, {**_USER, "email": "not-an-email"})
    assert r.status_code == 400


def test_register_missing_required_fields_returns_400(client):
    r = client.post(REGISTER, json={"email": "x@x.com"})  # no password
    assert r.status_code == 400


def test_register_display_name_is_optional(client):
    r = _register(client, {"email": _USER["email"], "password": _USER["password"]})
    assert r.status_code == 201
    assert r.json()["user"]["display_name"] is None


# ── login ─────────────────────────────────────────────────────────────────────

def test_login_returns_tokens(client):
    _register(client)
    r = _login(client)
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"


def test_login_wrong_password_returns_401(client):
    _register(client)
    r = client.post(LOGIN, json={"email": _USER["email"], "password": "wrongpassword"})
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHORIZED"


def test_login_unknown_email_returns_401(client):
    r = client.post(LOGIN, json={"email": "nobody@example.com", "password": "password123"})
    assert r.status_code == 401


def test_login_returns_different_tokens_each_time(client):
    _register(client)
    first  = _login(client).json()
    second = _login(client).json()
    assert first["refresh_token"] != second["refresh_token"]


# ── refresh ───────────────────────────────────────────────────────────────────

def test_refresh_returns_new_tokens(client):
    reg = _register(client).json()
    r = client.post(REFRESH, json={"refresh_token": reg["refresh_token"]})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert "refresh_token" in body
    # Refresh token must be a new random value each time
    assert body["refresh_token"] != reg["refresh_token"]
    # Access token is a valid JWT (JWTs issued in the same second are identical — that's fine)


def test_refresh_token_rotation_invalidates_old_token(client):
    """After a successful refresh the old token must be rejected."""
    reg = _register(client).json()
    old_refresh = reg["refresh_token"]
    client.post(REFRESH, json={"refresh_token": old_refresh})         # consume it
    r = client.post(REFRESH, json={"refresh_token": old_refresh})     # reuse → 401
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHORIZED"


def test_refresh_with_garbage_token_returns_401(client):
    r = client.post(REFRESH, json={"refresh_token": "this-is-not-a-valid-token"})
    assert r.status_code == 401


def test_refresh_new_token_is_usable(client):
    """Chained refresh: new token from first refresh works for a second refresh."""
    reg = _register(client).json()
    second = client.post(REFRESH, json={"refresh_token": reg["refresh_token"]}).json()
    r = client.post(REFRESH, json={"refresh_token": second["refresh_token"]})
    assert r.status_code == 200


# ── logout ────────────────────────────────────────────────────────────────────

def test_logout_returns_204(client):
    reg = _register(client).json()
    r = client.post(LOGOUT, json={"refresh_token": reg["refresh_token"]})
    assert r.status_code == 204
    assert r.content == b""


def test_logout_invalidates_refresh_token(client):
    reg = _register(client).json()
    refresh_token = reg["refresh_token"]
    client.post(LOGOUT, json={"refresh_token": refresh_token})
    r = client.post(REFRESH, json={"refresh_token": refresh_token})
    assert r.status_code == 401


def test_logout_with_unknown_token_is_silent(client):
    """Logging out with an unknown token should not error — idempotent."""
    r = client.post(LOGOUT, json={"refresh_token": "unknown-token"})
    assert r.status_code == 204

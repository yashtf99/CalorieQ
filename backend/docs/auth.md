# CalorieQ — Auth Design

## Token architecture

Two-token scheme: a short-lived **access token** for every API call, and a long-lived **refresh token** to get new access tokens without re-entering credentials.

| Token | Type | Lifetime | Stored where |
|---|---|---|---|
| Access | JWT (HS256) | 24 h | Client memory only |
| Refresh | Opaque random string | 30 days | `refresh_tokens` table (SHA-256 hash) |

**Why two tokens?**  
A single long-lived JWT cannot be invalidated — once issued, it's valid until expiry. By keeping the access token short-lived and validating the refresh token against the DB on every rotation, we can revoke sessions server-side (logout, account deletion, compromised token).

**Why opaque refresh tokens instead of a refresh JWT?**  
Refresh tokens are always validated against the DB anyway (to check revocation), so encoding claims in a JWT buys nothing. An opaque random string (`secrets.token_urlsafe(32)`) is simpler and its value gives no information to an attacker who intercepts it.

---

## Token lifecycle

```
Register / Login
     │
     ▼
Issue access_token (JWT, 24 h)   ←── returned to client
Issue refresh_token (random)     ←── returned to client; SHA-256 hash stored in DB
     │
     │  (client uses access_token on every request)
     │
     ▼  (access_token about to expire)
POST /auth/refresh  { refresh_token }
     │
     ├── Look up SHA-256(refresh_token) in DB
     ├── Check: not revoked, not expired
     ├── Revoke old refresh_token row  ← rotation
     ├── Issue new access_token
     └── Issue new refresh_token  ──► returned to client; new hash stored in DB
     │
     ▼  (user logs out)
POST /auth/logout  { refresh_token }
     │
     └── Mark refresh_token row as revoked=1
         (access_token runs out naturally — 24 h max)
```

---

## Valid flows

### Registration

```
Client                              Server
  │                                   │
  │  POST /auth/register              │
  │  { email, password, display_name }│
  │ ──────────────────────────────► │
  │                                   │  1. Check email not already registered
  │                                   │  2. bcrypt-hash password (cost factor 12)
  │                                   │  3. Insert user row
  │                                   │  4. Generate access_token (JWT)
  │                                   │  5. Generate refresh_token (random)
  │                                   │  6. Store SHA-256(refresh_token) in DB
  │  201 { user, access_token,        │
  │        refresh_token }            │
  │ ◄────────────────────────────── │
```

### Login

Identical to registration from step 4 onward — no new user row is inserted.

### Authenticated request

```
Client                              Server
  │                                   │
  │  GET /any-protected-route         │
  │  Authorization: Bearer <JWT>      │
  │ ──────────────────────────────► │
  │                                   │  1. Decode JWT with SECRET_KEY
  │                                   │  2. Verify typ == "access" claim
  │                                   │  3. Check exp (jose handles this)
  │                                   │  4. Load user from DB by sub (user_id)
  │  200 { ... }                      │
  │ ◄────────────────────────────── │
```

No DB hit on the refresh_tokens table for normal requests — access token validation is pure crypto.

### Token refresh

```
Client                              Server
  │                                   │
  │  POST /auth/refresh               │
  │  { refresh_token: "abc..." }      │
  │ ──────────────────────────────► │
  │                                   │  1. Compute SHA-256("abc...")
  │                                   │  2. SELECT row WHERE token_hash = hash
  │                                   │  3. Assert: row exists
  │                                   │  4. Assert: revoked = 0
  │                                   │  5. Assert: expires_at > now (UTC)
  │                                   │  6. SET revoked = 1  ← rotation
  │                                   │  7. Issue new access_token + refresh_token
  │                                   │  8. Store new hash in DB
  │  200 { access_token,              │
  │        refresh_token }            │
  │ ◄────────────────────────────── │
```

### Logout

```
Client                              Server
  │                                   │
  │  POST /auth/logout                │
  │  { refresh_token: "abc..." }      │
  │ ──────────────────────────────► │
  │                                   │  1. Compute SHA-256("abc...")
  │                                   │  2. SET revoked = 1 WHERE token_hash = hash
  │                                   │     (no-op if token unknown — silent)
  │  204 No Content                   │
  │ ◄────────────────────────────── │
```

Access token continues to work until its 24 h expiry. This is acceptable — the window is short and bounded.

---

## Attack mitigations

### Credential brute force

**Threat:** Attacker submits thousands of email/password guesses against `/auth/login`.

**Mitigation:** Passwords are SHA-256 pre-hashed before bcrypt. This sidesteps bcrypt's 72-byte truncation (see below) and still produces ~100–200 ms per verification. This does not replace rate limiting — rate limiting is a planned addition.

---

### Stolen access token (JWT replay)

**Threat:** Attacker intercepts a JWT and replays it.

**Mitigation:**
- Access tokens live for 24 h maximum. The blast radius is bounded.
- JWTs carry a `type: "access"` claim. The decode step explicitly checks this — a refresh token cannot be used as an access token and vice versa.
- All traffic must use HTTPS in production — tokens must never travel over plain HTTP.

There is no server-side access token blacklist (it would require a Redis lookup on every request and eliminate the stateless advantage of JWTs). The 24 h window is the accepted trade-off. Shortening `ACCESS_TOKEN_EXPIRE_MINUTES` in `.env` reduces exposure.

---

### Stolen refresh token (replay before logout)

**Threat:** Attacker steals a refresh token and uses it to get a long-lived session.

**Mitigation — token rotation:**  
Every `/auth/refresh` call revokes the submitted token and issues a new one. If an attacker uses a stolen token, the legitimate user's next refresh call will be rejected (the token was already rotated by the attacker). This signals the compromise and forces re-login.

```
Legitimate user has:   refresh_A
Attacker steals:       refresh_A

Attacker calls /refresh(refresh_A)
→ refresh_A revoked, attacker gets refresh_B

Legitimate user calls /refresh(refresh_A)
→ REJECTED (revoked) — user must re-login
→ (at this point attacker's refresh_B is also at risk but user can change password)
```

---

### Token storage in the DB (hash inversion)

**Threat:** DB is breached; attacker reads `refresh_tokens` table and replays tokens.

**Mitigation:** Only the `SHA-256` hash of the refresh token is stored, not the raw value. `secrets.token_urlsafe(32)` produces 256 bits of entropy — brute-forcing SHA-256 on a value that large is computationally infeasible. Even with full DB read access, the attacker cannot reconstruct the original token.

---

### bcrypt 72-byte truncation

**Threat:** bcrypt silently truncates passwords at 72 bytes, meaning two passwords that share the same first 72 chars hash identically.

**Mitigation:** Passwords are pre-hashed with SHA-256 (`hashlib.sha256(password.encode()).digest()`) before being passed to bcrypt. SHA-256 always produces a 32-byte output regardless of input length, so bcrypt's limit is never reached. Verified by regression test `test_password_longer_than_72_bytes_is_not_truncated`.

---

### Password enumeration

**Threat:** Attacker probes `/auth/login` to determine which emails are registered.

**Mitigation:** The same `401 UNAUTHORIZED — "Invalid email or password"` error is returned whether the email does not exist or the password is wrong. No information about account existence is leaked.

---

### JWT algorithm confusion (alg: none / RS256 downgrade)

**Threat:** Attacker crafts a JWT with `"alg": "none"` or switches the algorithm to one where they hold the key.

**Mitigation:** `jose.jwt.decode` is called with `algorithms=[settings.ALGORITHM]` — an explicit allowlist containing only `HS256`. Any token signed with a different algorithm is rejected before payload inspection. `alg: none` is not in the allowlist and is rejected.

---

### Account deletion cascade

When `DELETE /users/me` is called, the `users` row is deleted. All `refresh_tokens` rows for that user are cascade-deleted by the FK constraint (`ON DELETE CASCADE`). There is no window where an orphaned refresh token could be used to authenticate as a deleted account.

---

## What is NOT protected here (known gaps)

| Gap | Planned mitigation |
|---|---|
| No per-IP or per-user rate limiting on login/register | Add middleware (e.g. `slowapi`) before launch |
| Access token has no server-side revocation | Acceptable for 24 h window; add Redis blacklist if needed for immediate revocation |
| No MFA | Out of scope for v1 |
| Refresh token expiry is not sliding | A 30-day token issued on Jan 1 expires Jan 31 regardless of activity. Acceptable for MVP. |

# comdirect REST API — Authentication

The full auth flow requires 5 API calls. The entered TAN doubles as a Session-TAN — all subsequent transactions in the session require no additional TAN.

**Token endpoint:** `https://api.comdirect.de/oauth/token` (not under `/api/`)

---

## Overview: 5-Step Flow

```
Step 1: POST /oauth/token          → access_token (scope=TWO_FACTOR)
Step 2: GET  /session/.../sessions → Session object (identifier)
Step 3: POST /session/.../validate → TAN challenge in x-once-authentication-info
Step 4: PATCH /session/.../sessions/{id} + TAN → Session-TAN activated
Step 5: POST /oauth/token (cd_secondary) → access_token (scope=BANKING_RO BROKERAGE_RW ...)
```

---

## Step 1: OAuth2 Resource Owner Password Credentials Flow

**POST** `https://api.comdirect.de/oauth/token`

Request headers:
```http
Accept: application/json
Content-Type: application/x-www-form-urlencoded
```

Request body (form-encoded):
```
client_id=<client_id>
client_secret=<client_secret>
grant_type=password
username=<8-digit account number>
password=<6-digit PIN>
```

Response body:
```json
{
  "access_token": "1234567890_Access-Token_NEU_34567890",
  "token_type": "bearer",
  "refresh_token": "1234567890_Refresh-Token_NEU_4567890",
  "expires_in": 599,
  "scope": "TWO_FACTOR",
  "kdnr": "1234567890",
  "bpid": "1234567",
  "kontaktId": "1234567890"
}
```

> Use the returned `access_token` as `Authorization: Bearer {token}` in all subsequent requests.

---

## Step 2: Get Session Status

**GET** `/session/clients/user/v1/sessions`

Request headers:
```http
Accept: application/json
Authorization: Bearer {access_token}
Content-Type: application/json
x-http-request-info: {"clientRequestId":{"sessionId":"...","requestId":"..."}}
```

Response: Array of Session objects.

### Session Object

| Field | Type | Access | Description |
|-------|------|--------|-------------|
| `identifier` | String(≤40) | read-only | UUID of the session |
| `sessionTanActive` | Boolean | read-only | `true` if a Session-TAN is active |
| `activated2FA` | Boolean | read-only | `true` if 2FA was performed |

HTTP status: `200 OK`, `422 Unprocessable Entity`

---

## Step 3: Request TAN Challenge (Validate Session)

**POST** `/session/clients/user/v1/sessions/{sessionId}/validate`

Path parameter `sessionId` = `identifier` from Step 2.

Request body:
```json
{
  "identifier": "12345___identifier_der_session__1234",
  "sessionTanActive": true,
  "activated2FA": true
}
```

Response header contains TAN challenge:
```json
// x-once-authentication-info:
{
  "id": "7654321",
  "typ": "M_TAN",
  "challenge": "+49-160-99XXXX",
  "availableTypes": ["P_TAN", "M_TAN"]
}
```

### TAN Challenge Fields

| Field | Description |
|-------|-------------|
| `id` | Challenge ID — **must be passed to Step 4** |
| `typ` | TAN type: `M_TAN`, `P_TAN`, `P_TAN_PUSH` |
| `challenge` | P_TAN: PNG Base64-encoded image; M_TAN: phone number; P_TAN_PUSH: absent |
| `availableTypes` | All activated TAN methods for this account |

**To switch TAN method**, call this endpoint again with header:
```http
x-once-authentication-info: {"typ":"P_TAN"}
```

> **Warning:** 5 TAN challenges without a correct TAN in between → account locked.

HTTP status: `201 Created`, `422 Unprocessable Entity`

---

## Step 4: Activate Session-TAN

**PATCH** `/session/clients/user/v1/sessions/{sessionId}`

Request headers (additional):
```http
x-once-authentication-info: {"id":"7654321"}
x-once-authentication: 123456
```

> For `P_TAN_PUSH`: approval happens in the app. Omit `x-once-authentication` header entirely.

Request body (same as Step 3):
```json
{
  "identifier": "12345___identifier_der_session__1234",
  "sessionTanActive": true,
  "activated2FA": true
}
```

> **Warning:** 3 wrong TANs → account locked. After 2 errors, correct TAN on comdirect website resets the counter.

After activation:
- Session-TAN remains valid as long as the access/refresh tokens are valid.
- TAN-required transactions no longer need a TAN (`typ: TAN_FREI`).

HTTP status: `200 OK`, `422 Unprocessable Entity`

---

## Step 5: CD Secondary Flow (Final Token)

**POST** `https://api.comdirect.de/oauth/token`

Request headers:
```http
Accept: application/json
Content-Type: application/x-www-form-urlencoded
```

Request body:
```
client_id=<client_id>
client_secret=<client_secret>
grant_type=cd_secondary
token=<access_token from Step 1>
```

Response body:
```json
{
  "access_token": "1234567890__Access-Token__1234567890",
  "token_type": "bearer",
  "refresh_token": "1234567890_Refresh-Token__1234567890",
  "expires_in": 599,
  "scope": "BANKING_RO BROKERAGE_RW SESSION_RW",
  "kdnr": "1234567890",
  "bpid": "1234567",
  "kontaktId": "1234567890"
}
```

**This token provides access to all banking and brokerage APIs.**

### Available Scopes

| Scope | Access |
|-------|--------|
| `BANKING_RO` | Banking read (accounts, transactions) |
| `BROKERAGE_RW` | Brokerage read/write (depot, orders, quotes) |
| `MESSAGES_RO` | Documents/PostBox read |
| `SESSION_RW` | Session management |
| `REPORTS_RO` | Reports read |

---

## Token Refresh

**POST** `https://api.comdirect.de/oauth/token`

Token validity: ~10 minutes. Refresh before expiry.

Request body:
```
client_id=<client_id>
client_secret=<client_secret>
grant_type=refresh_token
refresh_token=<refresh_token>
```

Response: new `access_token` + `refresh_token` (same structure as Step 5).

> Session-TAN remains valid after token refresh.
> Only refresh when the current access token expires — not after every request.

---

## Token Revoke

**DELETE** `https://api.comdirect.de/oauth/revoke`

Request headers:
```http
Accept: application/json
Content-Type: application/x-www-form-urlencoded
Authorization: Bearer {access_token}
```

Response: `204 No Content` (empty body)

Invalidates both access token and refresh token. Session-TAN also becomes invalid.

---

## Transaction Authorization (with Session-TAN)

After Session-TAN is active, write operations (orders, etc.) use a 2-call pattern:

### 1. Validation call → TAN challenge

Response header:
```json
// x-once-authentication-info:
{
  "id": "7654321",
  "typ": "TAN_FREI",
  "availableTypes": ["M_TAN", "P_TAN"]
}
```

`TAN_FREI` means Session-TAN is active — no actual TAN input required.

### 2. Execution call

Request header only needs challenge ID:
```http
x-once-authentication-info: {"id":"7654321"}
```

No `x-once-authentication` header needed (Session-TAN already active).

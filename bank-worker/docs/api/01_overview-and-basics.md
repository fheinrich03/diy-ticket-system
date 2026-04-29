# comdirect REST API — Overview & Basics

**Version:** April 2020
**Base URL:** `https://api.comdirect.de/api`

---

## 1. URI Structure

```
https://api.comdirect.de/api/{module}/v{N}/{resource}/{id}
```

| Part       | Description |
|------------|-------------|
| URL-Prefix | Always `https://api.comdirect.de/api/` |
| Module     | Domain: `banking`, `brokerage`, `messages`, `reports`, `session` |
| Version    | `v` + ordinal number (MAJOR version), placed before resource |
| Resource   | Lowercase, plural (e.g. `orders`, `accounts`) |
| Id         | UUID identifying a specific resource |

**Example:**
```
https://api.comdirect.de/api/brokerage/v1/orders/{orderId}
```

---

## 2. HTTP Headers

### 2.1 Standard Request Headers (all authenticated endpoints)

```http
Accept: application/json
Content-Type: application/json
Authorization: Bearer {access_token}
x-http-request-info: {"clientRequestId":{"sessionId":"...","requestId":"..."}}
```

### 2.2 Custom Headers

| Header | Type | Description |
|--------|------|-------------|
| `x-http-request-info` | JSON object | **Mandatory.** Contains `clientRequestId` with `sessionId` and `requestId`. |
| `x-once-authentication-info` | JSON object | TAN challenge info (in responses) or challenge reference (in requests). |
| `x-once-authentication` | String | The actual TAN value (only needed if no Session-TAN active). |
| `x-http-response-info` | JSON object | Response header containing `BusinessMessage` array (errors/warnings/info). |
| `X-HTTP-Method-Override` | String | For clients that don't support all HTTP methods. Values: `PUT`, `PATCH`, `DELETE`. Optional. |

### 2.3 Client Request-Id

The `x-http-request-info` header must always be included:

```json
{
  "clientRequestId": {
    "sessionId": "550e8400e29b11d4a716446655440000",
    "requestId": "140113250"
  }
}
```

| Field | Format | Description |
|-------|--------|-------------|
| `sessionId` | String, max 32 chars, hex | Represents a user session. Generate once per session start, reuse for all requests. |
| `requestId` | 9-digit unsigned number | Unique within session. Can be timestamp as `HHmmssSSS`. |

Used for idempotency guarantees.

### 2.4 Transaction Headers (write operations)

When executing a transaction with Session-TAN active:

```http
x-once-authentication-info: {"id":"challengeId"}
```

When no Session-TAN active (also include TAN):

```http
x-once-authentication-info: {"id":"challengeId"}
x-once-authentication: 123456
```

---

## 3. Projections (Query Parameters)

| Parameter | Format | Description |
|-----------|--------|-------------|
| `with-attr` | String (comma-separated) | Attributes to **include** in response (normally excluded). |
| `without-attr` | String (comma-separated) | Attributes to **exclude** from response (normally included). |

Each API defines which attributes support these parameters.

---

## 4. Error Handling

Errors, warnings, and info messages are returned in the `x-http-response-info` response header as a `BusinessMessage`. On error (`severity=ERROR`), the response body is also replaced by the error message.

### x-http-response-info (header)

```json
{
  "messages": [
    {
      "severity": "INFO",
      "key": "hinweis_basisinformationsblatt_vorhanden",
      "message": "Hinweis: Das Basisinformationsblatt ist vorhanden.",
      "args": {},
      "origin": []
    },
    {
      "severity": "ERROR",
      "key": "fehler-erforderliche-tgf-fehlt",
      "message": "Für das von Ihnen gewünschte Wertpapier ...",
      "args": {},
      "origin": []
    }
  ]
}
```

### Error Response Body

```json
{
  "code": "request.object.invalid",
  "messages": [...]
}
```

### BusinessMessage Fields

| Field | Type | Description |
|-------|------|-------------|
| `severity` | String | `ERROR`, `WARN`, or `INFO` |
| `key` | String | Unique message key for client-side mapping (e.g. i18n) |
| `message` | String | Default German text with args already substituted |
| `args` | Object (Map) | Arguments used in message, e.g. `{"handelswaehrung": "EUR", "mindestbetrag": "41.50"}` |
| `origin` | String[] | Input field(s) the message relates to; empty for general errors |

> **Note:** Error messages are in German.

**Use `code` to control application flow. Use `message` only for display.**

### Common HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 204 | No Content |
| 400 | Bad Request |
| 404 | Not Found |
| 406 | Not Acceptable (wrong Accept header for document) |
| 422 | Unprocessable Entity (illegal argument or illegal state) |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

---

## 5. Standard Data Types

### 5.1 AmountValue

```json
{
  "value": "1234.56",
  "unit": "EUR"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `value` | AmountString | Nominal in the given unit |
| `unit` | String(3) | ISO-4217 currency (`EUR`, `USD`, ...) or special: `XXX` (pieces), `XXC` (percent), `XXM` (per mil), `XXP` (points), `XXU` (unknown) |

### 5.2 AmountString

JSON string representing a decimal (like Java `BigDecimal`). Format:
- Optional leading `-` (no `+`, no leading spaces)
- Decimal digits, no leading zeros (except `0.xx`)
- Optional `.` with at least one decimal place
- No thousands separators or spaces

Usage with explicit precision: `$AmountString[13+2]` (13 integer + 2 decimal places).

### 5.3 EnumText

```json
{
  "key": "LIMIT",
  "text": "Limitorder"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `key` | String(≤40) | Unique enum key |
| `text` | String(≤65) | Display text in German |

### 5.4 PercentageString

An AmountString representing a percentage (0–100). Default: `AmountString[3+3]`. Can be specified as `PercentageString[5]` for 5 decimal places.

### 5.5 CurrencyString

3-letter ISO-4217 currency code, e.g. `EUR`.

### 5.6 Date/Time Types

| Type | Format | Example |
|------|--------|---------|
| `DateString` | `YYYY-MM-DD` | `2020-04-01` |
| `DateTimeString` | `YYYY-MM-DDThh:mm:ss+zz` | `2020-04-01T09:30:00+02` |
| `TimestampString` | `YYYY-MM-DDThh:mm:ss,ffffff+zz` | `2020-04-01T09:30:00,123456+02` |

| Component | Description |
|-----------|-------------|
| `YYYY` | 4-digit year |
| `MM` | 2-digit month (01–12) |
| `DD` | 2-digit day (01–31); valuta dates may have impossible dates like 30.02 |
| `T` | Separator |
| `hh:mm:ss` | 2-digit hour/minute/second |
| `ffffff` | Up to 6 fractional seconds |
| `zz` | Timezone: `01` = CET (MEZ), `02` = CEST (MESZ) |

---

## 6. Paging Pattern

List responses use a standard paging envelope:

```json
{
  "paging": {
    "index": 0,
    "matches": 42
  },
  "aggregated": {...},
  "values": [...]
}
```

| Field | Description |
|-------|-------------|
| `paging.index` | Index of first returned item |
| `paging.matches` | Total number of matching items |
| `aggregated` | Optional aggregated data object (resource-specific) |
| `values` | Array of result objects |

Query parameters for paging:
- `paging-first`: index of first item (default: 0)
- `paging-count`: max items to return

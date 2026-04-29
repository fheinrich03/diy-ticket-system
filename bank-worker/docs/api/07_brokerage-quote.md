# comdirect REST API — Resource QUOTE (Livetrading)

The Quote resource enables OTC livetrading (Request-for-Quote). TAN must be entered **before** the quote is requested.

**Required scope:** `BROKERAGE_RW`

---

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/brokerage/v3/quoteticket` | Validate quote request + request TAN challenge |
| PATCH | `/brokerage/v3/quoteticket/{quoteTicketId}` | Submit TAN for quote ticket |
| POST | `/brokerage/v3/quotes` | Send quote request to venue |

---

## Livetrading Flow (5 Steps)

```
Step 1: POST /quoteticket     → validate + get TAN challenge → returns quoteTicketId
Step 2: PATCH /quoteticket/{id} → submit TAN (via header)
Step 3: POST /quotes          → request quote → returns Quote with quoteId + price
Step 4: POST /orders/validation → validate QUOTE order (references quoteTicketId + quoteId)
Step 5: POST /orders          → place order (same body as step 4 + challenge header)
```

---

## Step 1: POST /brokerage/v3/quoteticket

Validate the quote request and trigger a TAN challenge.

**Request body** (Order object, minimal fields):
```json
{
  "depotId": "1234_depot_UUID_1234",
  "orderType": "QUOTE",
  "side": "BUY",
  "instrumentId": "WKN123",
  "quantity": {"value": "10", "unit": "XXX"},
  "venueId": "1234_venue_UUID_LIVETRADING_1234"
}
```

> `side` is optional in this step.

**Response header:**
```json
// x-once-authentication-info:
{"id": "1212121", "typ": "TAN_FREI"}
```

**Response body:** Order object + `quoteTicketId`:
```json
{
  "depotId": "1234_depot_UUID_1234",
  "orderType": "QUOTE",
  "side": "BUY",
  "instrumentId": "WKN123",
  "venueId": "1234_venue_UUID_LIVETRADING_1234",
  "quantity": {"value": "10", "unit": "XXX"},
  "quoteTicketId": "1233_quoteTicketId_1234"
}
```

HTTP status: `201 Created`, `422 Unprocessable Entity`

---

## Step 2: PATCH /brokerage/v3/quoteticket/{quoteTicketId}

Submit TAN for the quote ticket.

**Path parameter:** `quoteTicketId` from Step 1

**Request headers (additional):**
```http
x-once-authentication-info: {"id":"1212121"}
```

> For Session-TAN (`TAN_FREI`): no `x-once-authentication` needed.

**Request body:** empty

**Response:** empty (`204 No Content`)

HTTP status: `204 No Content`, `422 Unprocessable Entity`

---

## Step 3: POST /brokerage/v3/quotes

Send quote request to venue. Same body as Step 1.

**Request body:**
```json
{
  "depotId": "1234_depot_UUID_1234",
  "orderType": "QUOTE",
  "side": "BUY",
  "instrumentId": "WKN123",
  "quantity": {"value": "10", "unit": "XXX"},
  "venueId": "1234_venue_UUID_LIVETRADING_1234"
}
```

**Response body:** Quote object with price and validity:
```json
{
  "depotId": "1234_depot_UUID_1234",
  "side": "BUY",
  "instrumentId": "WKN123",
  "venueId": "1234_venue_UUID_LIVETRADING_1234",
  "quantity": {"value": "10", "unit": "XXX"},
  "quoteId": "1234_quoteId_1234",
  "validity": 5000,
  "creationDateTimeStamp": "2019-11-01T09:02:35,116000+01",
  "limit": {"value": "53.7700", "unit": "EUR"},
  "expectedValue": {"value": "537.70000", "unit": "EUR"}
}
```

HTTP status: `200 OK`, `422 Unprocessable Entity`

---

## Steps 4 & 5: Place Quote Order

After receiving the quote, proceed with standard order validation + placement (see `06_brokerage-order.md`), but add `quoteId` and `quoteTicketId` to the Order body.

**POST /brokerage/v3/orders/validation** (Step 4):

```json
{
  "depotId": "1234_depot_UUID_1234",
  "orderType": "QUOTE",
  "side": "BUY",
  "instrumentId": "WKN123",
  "quantity": {"value": "10", "unit": "XXX"},
  "venueId": "1234_venue_UUID_LIVETRADING_1234",
  "quoteId": "1234_quoteId_1234",
  "quoteTicketId": "1233_quoteTicketId_1234",
  "limit": {"value": "53.7700", "unit": "EUR"},
  "creationTimestamp": "2019-11-01T09:02:35,116000+01"
}
```

Response header: new TAN challenge (id `3434343`).

**POST /brokerage/v3/orders** (Step 5):

Same body + challenge header:
```http
x-once-authentication-info: {"id":"3434343"}
```

Both validation (step 4) and order placement (step 5) use the same body.

> Steps 4 & 5 can be executed back-to-back since the TAN was already consumed in Step 2.

---

## Objects

### Quote

| Field | Type | Description |
|-------|------|-------------|
| `depotId` | String(≤40) | Depot number |
| `instrumentId` | String(≤40) | WKN, ISIN, or UUID (returned in same format as input) |
| `venueId` | String(≤40) | Venue UUID |
| `side` | String(≤4) | `BUY` (Ask) or `SELL` (Bid) |
| `quantity` | AmountValue | Max quantity for which this quote is valid |
| `quoteId` | String | Quote ID to reference in order |
| `validity` | Integer | Quote validity in milliseconds |
| `creationDateTimeStamp` | TimestampString | Quote creation time |
| `limit` | AmountValue | Quoted price |
| `expectedValue` | AmountValue | Expected total value |

### Quote Order Constraints

When placing a QUOTE order, these fields must match the original quote request:
- `depotId`
- `side`
- `instrumentId`
- `venueId`
- `quantity`

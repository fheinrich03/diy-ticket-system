# comdirect REST API — Examples

---

## 1. Livetrading (Quote Order) — Full 5-Step Flow

### Step 1: Request TAN Challenge

**POST /brokerage/v3/quoteticket**

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

Response header:
```
x-once-authentication-info: {"id":"1212121","typ":"TAN_FREI"}
```

Response body:
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

---

### Step 2: Submit TAN

**PATCH /brokerage/v3/quoteticket/1233_quoteTicketId_1234**

Request header:
```
x-once-authentication-info: {"id":"1212121"}
```

Request body: empty

Response: `204 No Content` (empty)

---

### Step 3: Request Quote

**POST /brokerage/v3/quotes**

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

Response body:
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

---

### Step 4: Validate Quote Order

**POST /brokerage/v3/orders/validation**

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

Response header:
```
x-once-authentication-info: {"id":"3434343","typ":"TAN_FREI"}
```

Response body: same as request body.

---

### Step 5: Place Quote Order

**POST /brokerage/v3/orders**

Request header:
```
x-once-authentication-info: {"id":"3434343"}
```

Request body: identical to Step 4.

Response body:
```json
{
  "depotId": "1234_depot_UUID_1234",
  "settlementAccountId": "1234_account_UUID_1234",
  "orderId": "1234_order_UUID_1234",
  "creationTimestamp": "2019-11-01T09:02:35,116000+01",
  "legNumber": 1,
  "bestEx": false,
  "orderType": "QUOTE",
  "orderStatus": "EXECUTED",
  "side": "BUY",
  "instrumentId": "ISIN_1234",
  "venueId": "1234_venue_UUID_LIVETRADING_1234",
  "quantity": {"value": "10", "unit": "XXX"},
  "executedQuantity": {"value": "10", "unit": "XXX"},
  "validityType": "GTD",
  "validity": "2019-11-30",
  "expectedValue": {"value": "537.70000", "unit": "EUR"},
  "executions": [
    {
      "executionId": "1234_execution_UUID_1234",
      "executionNumber": 1,
      "executedQuantity": {"value": "10", "unit": "XXX"},
      "executionPrice": {"value": "53.7700", "unit": "EUR"},
      "executionTimestamp": null
    }
  ]
}
```

---

## 2. Order Examples

> Before placing orders: call `GET /brokerage/v3/orders/dimensions` to get venue UUIDs and verify which order types are available at each venue.

### 2.1 Market Order

```json
{
  "depotId": "1234_depot_UUID_1234",
  "side": "BUY",
  "instrumentId": "WKN123",
  "orderType": "MARKET",
  "quantity": {"value": "1", "unit": "XXX"},
  "venueId": "1234_venue_UUID_1234",
  "validityType": "GFD"
}
```

---

### 2.2 Day Limit Order (GFD)

```json
{
  "depotId": "1234_depot_UUID_1234",
  "side": "BUY",
  "instrumentId": "WKN123",
  "orderType": "LIMIT",
  "quantity": {"value": "1", "unit": "XXX"},
  "venueId": "1234_venue_UUID_1234",
  "limit": {"value": "1.50", "unit": "EUR"},
  "validityType": "GFD"
}
```

---

### 2.3 Day Stop Limit Order (GFD)

```json
{
  "depotId": "1234_depot_UUID_1234",
  "side": "SELL",
  "instrumentId": "WKN123",
  "orderType": "STOP_LIMIT",
  "quantity": {"value": "1", "unit": "XXX"},
  "venueId": "1234_venue_UUID_1234",
  "triggerLimit": {"value": "9.50", "unit": "EUR"},
  "limit": {"value": "9.00", "unit": "EUR"},
  "validityType": "GFD"
}
```

---

### 2.4 Trailing Stop Market (Absolute Distance)

Sell order that triggers when price drops by 1 EUR from current level.

```json
{
  "depotId": "1234_depot_UUID_1234",
  "side": "SELL",
  "instrumentId": "WKN123",
  "orderType": "TRAILING_STOP_MARKET",
  "quantity": {"value": "1", "unit": "XXX"},
  "venueId": "1234_venue_UUID_1234",
  "triggerLimit": {"value": "10", "unit": "EUR"},
  "triggerLimitDistAbs": {"value": "1", "unit": "EUR"},
  "validityType": "GFD"
}
```

---

### 2.5 Trailing Stop Limit (Relative Distance)

Sell order with 5.50% trailing distance and limit.

```json
{
  "depotId": "1234_depot_UUID_1234",
  "side": "SELL",
  "instrumentId": "WKN123",
  "orderType": "TRAILING_STOP_LIMIT",
  "quantity": {"value": "1", "unit": "XXX"},
  "venueId": "1234_venue_UUID_1234",
  "limit": {"value": "9", "unit": "EUR"},
  "triggerLimit": {"value": "10", "unit": "EUR"},
  "trailingLimitDistRel": {"preDecimalPlaces": "5", "decimalPlaces": "50"},
  "validityType": "GFD"
}
```

---

### 2.6 One Cancels Other (OCO)

Combination order: when one leg executes, the other is cancelled.

```json
{
  "depotId": "1234_depot_UUID_1234",
  "orderType": "ONE_CANCELS_OTHER",
  "subOrders": [
    {
      "depotId": "1234_depot_UUID_1234",
      "side": "SELL",
      "instrumentId": "WKN123",
      "orderType": "STOP_MARKET",
      "quantity": {"value": "1", "unit": "XXX"},
      "triggerLimit": {"value": "15.50", "unit": "XXX"},
      "venueId": "1234_venue_UUID_1234",
      "validityType": "GTD",
      "validity": "2019-12-01"
    },
    {
      "depotId": "1234_depot_UUID_1234",
      "side": "SELL",
      "instrumentId": "WKN123",
      "orderType": "LIMIT",
      "quantity": {"value": "1", "unit": "XXX"},
      "limit": {"value": "50", "unit": "XXX"},
      "venueId": "1234_venue_UUID_1234",
      "validityType": "GTD",
      "validity": "2019-12-01"
    }
  ]
}
```

---

### 2.7 Next Order (NEO)

Combination order: second leg activates after first leg executes.

```json
{
  "depotId": "1234_depot_UUID_1234",
  "orderType": "NEXT_ORDER",
  "subOrders": [
    {
      "depotId": "1234_depot_UUID_1234",
      "side": "BUY",
      "instrumentId": "WKN123",
      "orderType": "LIMIT",
      "quantity": {"value": "10", "unit": "XXX"},
      "limit": {"value": "10.00", "unit": "XXX"},
      "venueId": "1234_venue_UUID_1234",
      "validityType": "GTD",
      "validity": "2019-12-01"
    },
    {
      "depotId": "1234_depot_UUID_1234",
      "side": "SELL",
      "instrumentId": "WKN123",
      "orderType": "STOP_MARKET",
      "quantity": {"value": "5", "unit": "XXX"},
      "triggerLimit": {"value": "5.50", "unit": "XXX"},
      "venueId": "1234_venue_UUID_1234",
      "validityType": "GFD"
    }
  ]
}
```

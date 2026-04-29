# comdirect REST API — Resource ORDER

Place, modify, delete orders. Query order book and individual orders. Get ex-ante cost indication (MiFID II).

**Required scope:** `BROKERAGE_RW`

> **Note:** `venueId` required for order placement — get from `GET /brokerage/v3/orders/dimensions`.

---

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/brokerage/v3/orders/dimensions` | Tradable venues + order options for an instrument |
| GET | `/brokerage/depots/{depotId}/v3/orders` | Order book for a depot |
| GET | `/brokerage/v3/orders/{orderId}` | Single order |
| POST | `/brokerage/v3/orders/prevalidation` | Pre-validate new order (no TAN) |
| POST | `/brokerage/v3/orders/validation` | Validate new order + trigger TAN challenge |
| POST | `/brokerage/v3/orders/costindicationexante` | Ex-ante cost indication for new order |
| POST | `/brokerage/v3/orders` | Place order (requires TAN challenge from validation) |
| POST | `/brokerage/v3/orders/{orderId}/prevalidation` | Pre-validate order modification |
| POST | `/brokerage/v3/orders/{orderId}/validation` | Validate order modification/deletion + TAN |
| POST | `/brokerage/v3/orders/{orderId}/costindicationexante` | Ex-ante cost indication for modified order |
| PATCH | `/brokerage/v3/orders/{orderId}` | Modify order (requires TAN challenge) |
| DELETE | `/brokerage/v3/orders/{orderId}` | Delete order (requires TAN challenge) |

---

## GET /brokerage/v3/orders/dimensions

Get tradable venues and order types for an instrument.

**Query/Filter parameters:**

| Parameter | Description |
|-----------|-------------|
| `instrumentId` | Instrument UUID |
| `isin` | ISIN |
| `wkn` | WKN |
| `mnemonic` | Symbol |
| `venueId` | Filter to a specific venue UUID |
| `side` | `BUY` or `SELL` |
| `orderType` | `MARKET`, `LIMIT`, `QUOTE`, `STOP_MARKET`, `STOP_LIMIT`, `TRAILING_STOP_MARKET`, `TRAILING_STOP_LIMIT`, `ONE_CANCELS_OTHER`, `NEXT_ORDER` |
| `type` | `EXCHANGE` (stock exchange) or `OFF` (livetrading OTC) |
| `country` | Country code ISO 3166-2 |
| `custodyType` | e.g. `004` |

> Check response header for target market criteria and KID/BIB information before placing orders.

**Response:**
```json
{
  "paging": { "index": 0, "matches": 1 },
  "values": [ { /* Dimensions */ } ]
}
```

Always one element — a Dimensions object containing the list of venues.

HTTP status: `200 OK`, `422 Unprocessable Entity`

---

## GET /brokerage/depots/{depotId}/v3/orders

Get order book for a depot.

**Path parameters:**
- `depotId`: depot UUID

**Filter parameters:** `orderStatus`, `venueId`, `side`, `orderType`, `instrumentId`, `isin`, `wkn`, `min-creationTimeStamp`, `max-creationTimeStamp`

**Query parameters:**
- `without-attr=executions`: suppress Executions array
- `with-attr=instrument`: include Instrument data

**Response:**
```json
{
  "paging": { "index": 0, "matches": 5 },
  "values": [ { /* Order */ } ]
}
```

HTTP status: `200 OK`, `404 Not Found`, `422 Unprocessable Entity`

---

## GET /brokerage/v3/orders/{orderId}

Get single order by ID.

**Path parameters:**
- `orderId`: order UUID

**Query parameters:**
- `without-attr=executions`: suppress Executions array

HTTP status: `200 OK`, `404 Not Found`

---

## Order Lifecycle (New Order)

```
1. GET  /dimensions          → get venueId + available order types
2. POST /prevalidation       → validate fields during input (optional, no TAN)
3. POST /costindicationexante → view MiFID II cost breakdown (optional, no TAN)
4. POST /validation          → full validation + TAN challenge (x-once-authentication-info)
5. POST /orders              → place order with challenge ID in header
```

### Step 4 — Validation

Request body: Order object (full)
Response header contains TAN challenge:
```json
// x-once-authentication-info:
{"id": "7654321", "typ": "TAN_FREI"}
```

### Step 5 — Place Order

Additional request header:
```http
x-once-authentication-info: {"id":"7654321"}
```

Response: `201 Created` with Order object including `orderId`.

---

## Order Lifecycle (Modify Order)

```
1. POST /orders/{id}/prevalidation  → validate changes (optional)
2. POST /orders/{id}/validation     → validate + TAN challenge
3. PATCH /orders/{id}               → apply changes with challenge ID
```

**Modifiable fields:** `limit`, `validity` (validityType + validity date)

---

## Order Lifecycle (Delete Order)

```
1. POST /orders/{id}/validation  → body: {} (empty) → TAN challenge
2. DELETE /orders/{id}           → with challenge ID in header
```

---

## Objects

### Dimensions

| Field | Type | Description |
|-------|------|-------------|
| `venues` | Venue[] | List of tradable venues |

---

### Venue

| Field | Type | Description |
|-------|------|-------------|
| `venueId` | String(≤40) | Venue UUID |
| `name` | String(≤65) | Venue name |
| `type` | String(≤20) | `EXCHANGE`, `OFF`, `FUND` |
| `country` | String(2) | Country ISO 3166-2 (`DE`, `US`, `FR`, ...) |
| `currencies` | CurrencyString[] + NULL | Settlement currencies |
| `sides` | String(≤4)[] | `BUY`, `SELL` |
| `validityTypes` | String(3)[] | `GFD` (Good-for-day, default), `GTD` (Good-til-date) |
| `orderTypes` | Map | Map of order type name → type details |
| `orderTypes[].name` | String(≤30)[] | Order type names |
| `orderTypes[].limitExtensions` | String(≤3)[] + NULL | Limit extensions: `FOK`, `IOC`, `AON` |
| `orderTypes[].tradingRestrictions` | String(≤3)[] + NULL | Trading restrictions: `OAO`, `AO`, `CAO` |

**Limit Extensions:**
- `FOK`: Fill-or-Kill
- `IOC`: Immediate-or-Cancel
- `AON`: All-or-None

**Trading Restrictions:**
- `OAO`: Opening Auction Only
- `AO`: Auction Only
- `CAO`: Closing Auction Only

---

### Order

| Field | Type | Access | Description |
|-------|------|--------|-------------|
| `depotId` | String(≤40) | initial, mandatory | Depot UUID |
| `settlementAccountId` | String(≤40) + NULL | initial, optional | Settlement account UUID (if different from default) |
| `orderId` | String(≤40) | read-only | Order UUID |
| `creationTimestamp` | TimestampString | read-only | Order creation timestamp |
| `legNumber` | Integer | read-only | Leg order number (combination orders) |
| `bestEx` | Boolean | initial, optional | Best execution flag (auto-select venue). Default: `false`. If `true`, omit `venueId`. |
| `orderType` | String(≤30) | initial, mandatory | See Order Types below |
| `orderStatus` | String(≤30) | read-only | See Order Statuses below |
| `subOrders` | Order[] + NULL | initial, mandatory for combo | Sub-orders for OCO/NEXT_ORDER |
| `side` | String(≤4) | initial, mandatory | `BUY` or `SELL` |
| `instrumentId` | String(≤40) | initial, mandatory | WKN, ISIN, or UUID |
| `quoteTicketId` | String(≤40) | initial, mandatory for RfQ | Quote ticket ID reference |
| `quoteId` | String(≤40) | initial, mandatory for RfQ | Quote ID reference |
| `venueId` | String(≤40) + NULL | initial, mandatory (if bestEx=false) | Venue UUID |
| `quantity` | AmountValue | initial, mandatory | Units or nominal |
| `limitExtension` | String(≤3) + NULL | initial, optional | `FOK`, `IOC`, `AON` |
| `tradingRestriction` | String(≤3) + NULL | initial, optional | `OAO`, `AO`, `CAO` |
| `limit` | AmountValue + NULL | editable | Limit price (null for MARKET, STOP_MARKET, TRAILING_STOP_MARKET) |
| `triggerLimit` | AmountValue + NULL | editable | Stop trigger price (for STOP_LIMIT, STOP_MARKET, TRAILING_STOP, OCO) |
| `trailingLimitDistAbs` | AmountString + NULL | editable, optional | Trailing distance (absolute) |
| `trailingLimitDistRel` | PercentageString + NULL | editable, optional | Trailing distance (relative %) |
| `validityType` | String(3) + NULL | editable, optional | `GFD` (default) or `GTD` |
| `validity` | DateString + NULL | editable, optional | Date for GTD orders (`YYYY-MM-DD`) |
| `openQuantity` | AmountValue | read-only | Unfilled quantity |
| `cancelledQuantity` | AmountValue | read-only | Cancelled quantity |
| `executedQuantity` | AmountValue | read-only | Total executed quantity |
| `expectedValue` | AmountValue + NULL | read-only | Expected settlement amount for limit orders |
| `executions` | Execution[] | read-only | List of executions |

**Order Types:**
- `MARKET` — Market order
- `LIMIT` — Limit order
- `QUOTE` — Quote/RfQ (livetrading)
- `STOP_MARKET` — Stop market order
- `STOP_LIMIT` — Stop limit order
- `TRAILING_STOP_MARKET` — Trailing stop market
- `TRAILING_STOP_LIMIT` — Trailing stop limit
- `ONE_CANCELS_OTHER` — OCO combination order
- `NEXT_ORDER` — Next order combination

**Order Statuses:**

| Status | Description |
|--------|-------------|
| `PENDING` | Accepted, processing, or waiting (multiple sub-states) |
| `OPEN` | Open |
| `EXECUTED` | Fully executed |
| `SETTLED` | Settled |
| `CANCELLED_USER` | Cancelled by user |
| `EXPIRED` | Expired |
| `CANCELLED_SYSTEM` | Rejected or not executed by system |
| `CANCELLED_TRADE` | Trade cancellation |
| `UNKNOWN` | Overall status unclear |
| `PARTIALLY_EXECUTED` | Partially filled (openQuantity > 0 AND executedQuantity > 0) |
| `WAITING` | NEXT_ORDER second leg waiting |

---

### Execution

| Field | Type | Description |
|-------|------|-------------|
| `executionId` | String(≤40) | Execution UUID |
| `executionNumber` | Integer | Chronological rank of this execution |
| `executedQuantity` | AmountValue | Executed units or nominal |
| `executionPrice` | AmountValue | Execution price |
| `executionTimestamp` | TimestampString | Execution timestamp (MiFID II format) |

---

### CostIndicationExAnte

MiFID II pre-trade cost disclosure. Always read-only.

**Top-level fields:**

| Field | Type | Description |
|-------|------|-------------|
| `depotId` | String(≤40) | Depot UUID |
| `calculationSuccessful` | Boolean | If `false`, `linkCosts` contains fallback URL |
| `name` | String(≤60) | Instrument name |
| `wkn` | String(6) | WKN |
| `side` | String(≤4) | `BUY` or `SELL` |
| `quantity` | AmountValue | Order quantity |
| `limit` | AmountValue + NULL | Order limit |
| `expectedValue` | AmountValue | Expected settlement amount (net) |
| `venueName` | String(≤65) | Venue name |
| `settlementCurrency` | CurrencyString | Settlement currency |
| `tradingCurrency` | CurrencyString | Trading currency |
| `reportingCurrency` | CurrencyString | Reporting/accounting currency |
| `fxRate` | FXRateEUR + NULL | FX rate (trading currency ≠ EUR) |
| `expectedSettlementCosts` | AmountValue + NULL | Expected order costs billed to customer |
| `holdingPeriod` | AmountString + NULL | Assumed holding period in years (for BUY) |
| `totalCostsAbs` | AmountValue | Total costs (absolute) |
| `totalCostsRel` | PercentageString | Total costs as % of investment |
| `purchaseCosts` | CostGroup + NULL | Purchase costs (type=K, only for BUY) |
| `holdingCosts` | CostGroup + NULL | Holding costs per year (type=H, only for BUY) |
| `salesCosts` | CostGroup | Sales costs (type=V, both BUY and SELL) |
| `totalCostsDetail` | TotalCostBlock | Cost breakdown: own services (E), external services (F), product costs (P) |
| `totalHoldingCosts` | TotalHoldingCostBlock | Cost timeline (year 1, year 2, year of sale) — only for BUY |
| `linkCosts` | String(≤200) | URL to generic cost indication (fallback) |
| `linkKid` | String(≤200) | URL to KID (key information document) |

### FXRateEUR

FX rate for 1 EUR:

| Field | Type | Description |
|-------|------|-------------|
| `bid` | AmountValue | Bid rate (buy EUR, sell foreign) |
| `ask` | AmountValue | Ask rate (sell EUR, buy foreign) |

### CostGroup

| Field | Type | Description |
|-------|------|-------------|
| `type` | String(1) | `K` (purchase), `H` (holding), `V` (sales) |
| `label` | String(≤100) | Group label |
| `sum` | AmountValue + NULL | Total in trading currency |
| `sumReportingCurrency` | AmountValue | Total in reporting currency |
| `costs` | CostEntry[] + NULL | Individual cost entries |

### CostEntry

| Field | Type | Description |
|-------|------|-------------|
| `type` | String(1) | `E` (own services), `F` (external services), `P` (product costs) |
| `label` | String(≤100) | Entry label |
| `amount` | AmountValue + NULL | Amount in trading currency |
| `amountReportingCurrency` | AmountValue | Amount in reporting currency |
| `inducement` | Inducement + NULL | Third-party payment to bank |

### Inducement

| Field | Type | Description |
|-------|------|-------------|
| `amount` | AmountValue | Inducement amount |
| `estimated` | Boolean | `true` if this is an estimate |

### TotalCostBlock

| Field | Type | Description |
|-------|------|-------------|
| `serviceCosts` | TotalCostEntry | Own bank services (type=E) |
| `serviceInducement` | AmountValue | Total third-party payments for own services |
| `externalCosts` | TotalCostEntry | External services (type=F) |
| `productCosts` | TotalCostEntry | Product costs (type=P) |

### TotalCostEntry

| Field | Type | Description |
|-------|------|-------------|
| `type` | String(1) | `E`, `F`, or `P` |
| `label` | String(65) | Display label |
| `amount` | AmountValue | Total in reporting currency |
| `averageReturnPA` | PercentageString + NULL | Average annual % (shown for BUY only) |

### TotalHoldingCostBlock

| Field | Type | Description |
|-------|------|-------------|
| `year1` | TotalHoldingCostEntry | Costs in year 1 |
| `year2` | TotalHoldingCostEntry | Costs in year 2 |
| `sales` | TotalHoldingCostEntry | Costs in year of disposal |

### TotalHoldingCostEntry

| Field | Type | Description |
|-------|------|-------------|
| `type` | String(30) | `IM_ERSTEN_JAHR`, `IM_ZWEITEN_JAHR`, `IM_JAHR_DER_VERAUESSERUNG` |
| `amount` | AmountValue | Total costs in reporting currency |
| `averageReturnPA` | PercentageString | Average annual return impact |

# comdirect REST API — Resource DEPOT

Access depot balances, positions, and transaction history.

**Required scope:** `BROKERAGE_RW`

---

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/brokerage/clients/{clientId}/v3/depots` | List all depots |
| GET | `/brokerage/v3/depots/{depotId}/positions` | Depot positions (with optional aggregation) |
| GET | `/brokerage/v3/depots/{depotId}/positions/{positionId}` | Single position |
| GET | `/brokerage/v3/depots/{depotId}/transactions` | Depot transactions |

> `depotId` (UUID) can be retrieved from the depots endpoint.

---

## GET /brokerage/clients/{clientId}/v3/depots

List all depots for the user.

**Path parameters:**
- `clientId`: literal `"user"` (or customer UUID)

**Response:**
```json
{
  "paging": {
    "index": 0,
    "matches": 1
  },
  "values": [
    { /* Depot */ }
  ]
}
```

HTTP status: `200 OK`, `404 Not Found`, `422 Unprocessable Entity`

---

## GET /brokerage/v3/depots/{depotId}/positions

Retrieve all positions (or aggregated summary) for a depot.

**Path parameters:**
- `depotId`: depot UUID

**Query parameters:**

| Parameter | Description |
|-----------|-------------|
| `instrumentId` | Filter by WKN, ISIN, or instrument UUID |
| `with-attr=instrument` | Include Instrument objects in positions |
| `without-attr=depot` | Suppress Depot master data |
| `without-attr=positions` | Suppress positions list (return only aggregated totals) |

**Response:**
```json
{
  "paging": {
    "index": 0,
    "matches": 5
  },
  "aggregated": { /* DepotAggregation */ },
  "values": [
    { /* DepotPosition */ }
  ]
}
```

HTTP status: `200 OK`, `404 Not Found`, `422 Unprocessable Entity`, `503 Service Unavailable`

---

## GET /brokerage/v3/depots/{depotId}/positions/{positionId}

Retrieve a single depot position.

**Path parameters:**
- `depotId`: depot UUID
- `positionId`: position UUID

**Query parameters:**
- `with-attr=instrument`: include Instrument data
- `without-attr=depot`: suppress Depot master data
- `without-attr=positions`: suppress position data

**Response:**
```json
{
  "values": { /* DepotPosition */ }
}
```

HTTP status: `200 OK`, `404 Not Found`, `422 Unprocessable Entity`

---

## GET /brokerage/v3/depots/{depotId}/transactions

Retrieve depot transactions.

**Path parameters:**
- `depotId`: depot UUID

**Filter/Query parameters:**

| Parameter | Description |
|-----------|-------------|
| `wkn` | WKN filter |
| `isin` | ISIN filter |
| `instrumentId` | Instrument UUID filter |
| `min-bookingDate` | Earliest booking date: `YYYY-MM-DD` or relative offset like `-10d` (default: `-180d`) |
| `max-bookingDate` | Latest booking date: `YYYY-MM-DD` |
| `transactionDirection` | `IN`, `OUT` |
| `transactionType` | `BUY`, `SELL`, `TRANSFER_IN`, `TRANSFER_OUT` |
| `bookingStatus` | `BOOKED`, `NOTBOOKED`, `BOTH` |
| `min-transactionValue` | Minimum transaction value |
| `max-transactionValue` | Maximum transaction value |
| `without-attr=instrument` | Suppress Instrument data in transactions |

**Response:**
```json
{
  "paging": {
    "index": 0,
    "matches": 20
  },
  "values": [
    { /* DepotTransaction */ }
  ]
}
```

HTTP status: `200 OK`, `404 Not Found`, `422 Unprocessable Entity`

---

## Objects

### Depot

| Field | Type | Description |
|-------|------|-------------|
| `depotId` | String(≤40) | Depot UUID |
| `depotDisplayId` | String(7) | Depot number (display) |
| `clientId` | String(≤40) | Customer UUID |
| `defaultSettlementAccountId` | String(≤40) | Default settlement account UUID |
| `settlementAccountIds` | String(≤40)[] + NULL | List of additional settlement account UUIDs |

---

### DepotPosition

| Field | Type | Description |
|-------|------|-------------|
| `depotId` | String(≤40) | Depot UUID |
| `positionId` | String(≤40) | Position UUID |
| `wkn` | String(6) | WKN |
| `custodyType` | String(3) | Custody type |
| `quantity` | AmountValue | Number of units or nominal (for percentage notation) |
| `availableQuantity` | AmountValue | Tradable units (excl. blocked employee shares etc.) |
| `currentPrice` | Price | Current price (if available) |
| `purchasePrice` | AmountValue + NULL | Purchase price (if available) |
| `prevDayPrice` | Price + NULL | Previous day price (if available) |
| `currentValue` | AmountValue | Position value at current prices |
| `purchaseValue` | AmountValue + NULL | Average purchase value |
| `profitLossPurchaseAbs` | AmountValue + NULL | P&L vs. purchase price (absolute) |
| `profitLossPurchaseRel` | PercentageString + NULL | P&L vs. purchase price (percent) |
| `profitLossPrevDayAbs` | AmountValue + NULL | P&L vs. previous day (absolute) |
| `profitLossPrevDayRel` | PercentageString + NULL | P&L vs. previous day (percent) |
| `instrument` | Instrument | Instrument details |

> `quantity` uses decimal + unit (pieces, percent, currency, ...)
> `availableQuantity` excludes blocked/reserved units.

---

### DepotTransaction

| Field | Type | Description |
|-------|------|-------------|
| `transactionId` | String(≤40) | Transaction UUID |
| `bookingStatus` | String(≤10) | `BOOKED` or `NOTBOOKED` |
| `bookingDate` | DateString + NULL | Booking date |
| `businessDate` | DateString | Business date |
| `quantity` | AmountValue | Units or nominal |
| `instrumentId` | String(≤40) | Instrument UUID |
| `instrument` | Instrument + NULL | Instrument details |
| `executionPrice` | AmountValue | Execution price |
| `transactionValue` | AmountValue | Transaction value |
| `transactionDirection` | String(≤3) | `IN` or `OUT` |
| `transactionType` | EnumText | See table below |

**Transaction Type Values:**

| Key | German | English |
|-----|--------|---------|
| `SELL` | Verkauf | Sell |
| `OTHER` | Sonstige | Other |
| `BUY` | Kauf | Buy |
| `TRANSFER_IN` | Depotübertrag eingehend | Incoming securities account transfer |
| `TRANSFER_OUT` | Depotübertrag ausgehend | Outgoing securities account transfer |

---

### Price

| Field | Type | Description |
|-------|------|-------------|
| `price` | AmountValue | Quote/price value |
| `type` | String(≤5) | Price type: `LAST`, `BID`, `ASK`, `MID` |
| `quantity` | AmountValue + NULL | Units or nominal |
| `priceDateTime` | DateTimeString | Price timestamp `YYYY-MM-DDThh:mm:ss+zz` |

**Price Types:**

| Type | Description |
|------|-------------|
| `LAST` | Last established price (electronic or auction trading) |
| `BID` | Highest buy offer (electronic trading or market maker buy quote) |
| `ASK` | Lowest sell offer (electronic trading or market maker sell quote) |
| `MID` | Mid price between BID and ASK |

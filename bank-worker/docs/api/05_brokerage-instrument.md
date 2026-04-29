# comdirect REST API — Resource INSTRUMENT

Retrieve security/instrument information by WKN, ISIN, or symbol.

**Required scope:** `BROKERAGE_RW`

---

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/brokerage/v1/instruments/{instrumentId}` | Get instrument information |

---

## GET /brokerage/v1/instruments/{instrumentId}

Retrieve instrument master data.

**Path parameters:**
- `instrumentId`: WKN (6 chars), ISIN (12 chars), or mnemonic (symbol) — case-sensitive

**Query parameters:**

| Parameter | Description |
|-----------|-------------|
| `with-attr=orderDimensions` | Include OrderDimensions (tradable venues + order types) |
| `with-attr=fundDistribution` | Include FundDistribution data (only for funds) |
| `with-attr=derivativeData` | Include DerivativeData (only for derivatives) |
| `without-attr=staticData` | Suppress StaticData object |

> Multiple `with-attr` values: use repeated query params: `with-attr=orderDimensions&with-attr=fundDistribution`

**Response:**
```json
{
  "paging": {
    "index": 0,
    "matches": 1
  },
  "values": [
    { /* Instrument */ }
  ]
}
```

Always returns exactly one element in `values`.

HTTP status: `200 OK`, `404 Not Found`, `422 Unprocessable Entity`

---

## Objects

### Instrument

| Field | Type | Description |
|-------|------|-------------|
| `instrumentId` | String(≤40) + NULL | Instrument UUID |
| `wkn` | String(6) | WKN |
| `mnemonic` | String(≤5) + NULL | Ticker symbol |
| `isin` | String(12) | ISIN |
| `name` | String(≤60) | Full name |
| `shortName` | String(≤25) | Short name |
| `staticData` | StaticData + NULL | Static data (notation, type, flags) |
| `orderDimensions` | Dimensions + NULL | Tradable venues and order dimensions |
| `fundsDistribution` | FundDistribution + NULL | Fund-specific data (if instrument is a fund) |
| `derivativeData` | DerivativeData + NULL | Derivative-specific data |

---

### StaticData

| Field | Type | Description |
|-------|------|-------------|
| `notation` | String(3) | Unit of quotation: `XXX` (STK), `XXC` (PRZ/percent), `XXM` (PRM/per mil), `XXP` (PKT/points), `XXU` (UNB/unknown) |
| `currency` | CurrencyString | Depot currency (ISO 4217 + `XXX`, `XXP`, `XXU`) |
| `instrumentType` | String(≤30) | Security type (see table below) |
| `priipsRelevant` | Boolean | Whether PRIIPs regulation applies |
| `kidAvailable` | Boolean | Whether a KID (key information document) is available — show static hint before order |
| `shippingWaiverRequired` | Boolean | For funds: must show waiver checkbox for fund sales documents |
| `fundRedemptionLimited` | Boolean | Flag for open-ended real estate funds with limited redemption |

**Instrument Types:**

| Key | German |
|-----|--------|
| `SHARE` | AKTIE |
| `BONDS` | ANLEIHE |
| `SUBSCRIPTION_RIGHT` | BEZUGSRECHT |
| `ETF` | ETF |
| `PROFIT_PART_CERTIFICATE` | GENUSSCHEIN |
| `FUND` | FONDS |
| `WARRANT` | OPTIONSSCHEIN |
| `CERTIFICATE` | ZERTIFIKAT |
| `NOT_AVAILABLE` | NICHT_VERFUEGBAR |

---

### DerivativeData

Additional data for derivative instruments.

| Field | Type | Description |
|-------|------|-------------|
| `underlyingInstrument` | Instrument + NULL | Underlying instrument |
| `underlyingPrice` | Price + NULL | Current price of underlying |
| `certificateType` | String + NULL | Certificate type (Hebel, Index, Basket, Discount, Bonus, Kapitalschutz, ...) |
| `rating` | Rating + NULL | Rating |
| `strikePrice` | AmountValue | Strike/base price |
| `leverage` | String + NULL | Leverage factor |
| `multiplier` | String + NULL | Subscription ratio |
| `expiryDate` | DateString + NULL | Expiry date |
| `yieldPA` | PercentageString + NULL | Yield p.a. |
| `remainingTermInYears` | AmountString + NULL | Remaining term (expiryDate - today) |
| `nominalRate` | PercentageString + NULL | Nominal interest rate |
| `warrantType` | String + NULL | Warrant type: `Call` or `Put` |
| `maturityDate` | DateString + NULL | Maturity date (primarily bonds) |
| `interestPaymentDate` | DateString + NULL | Coupon/interest payment date |
| `interestPaymentInterval` | String + NULL | `ANNUALLY`, `SEMIANNUALLY`, `QUARTERLY`, `MONTHLY`, `OTHER` |

---

### Rating

| Field | Type | Description |
|-------|------|-------------|
| `morningstar` | String + NULL | Morningstar rating (funds) |
| `moodys` | String + NULL | Moody's rating (bonds) |

---

### FundDistribution

| Field | Type | Description |
|-------|------|-------------|
| `currency` | CurrencyString | ISO 4217 currency |
| `regularIssueSurcharge` | PercentageString | Regular front-end load |
| `discountIssueSurcharge` | PercentageString | Discounted front-end load |
| `reducedIssueSurcharge` | PercentageString | Reduced front-end load |
| `investmentCategory` | String | Investment category (see list below) |
| `totalExpenseRatio` | PercentageString | TER (ongoing charges) in % |
| `rating` | Rating + NULL | Fund rating |

**Investment Categories:**
- Aktienfonds, Aktien
- Rentenfonds, Renten
- Geldmarktfonds, Geldmarkt
- Gemischte Fonds
- Dachfonds
- Immobilienfonds
- Alternative Fonds
- Strukturierte Fonds
- Alternative Investments
- sonstige ETF's

# comdirect REST API — Resource REPORTS

Retrieve balances across all comdirect products (accounts, depot, cards, loans, savings).

**Required scope:** `REPORTS_RO`

---

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/reports/participants/{participantId}/v1/allbalances` | All product balances |

---

## GET /reports/participants/{participantId}/v1/allbalances

Retrieve balances for all comdirect products of the user.

**Path parameters:**
- `participantId`: literal `"user"` or participant UUID

**Filter parameters:**

| Parameter | Values | Description |
|-----------|--------|-------------|
| `clientConnectionType` | `CURRENT_CLIENT`, `OTHER_COMDIRECT` | Filter by connection type |
| `productType` | `ACCOUNT`, `CARD`, `DEPOT`, `LOAN`, `SAVINGS` | Filter by product type(s) |
| `targetClientId` | UUID(s) | Filter by specific customer connection UUIDs |

**Query parameters:**
- `without-attr=balance.staticdata`: suppress master data in balance objects

**Response:**
```json
{
  "paging": {
    "index": 0,
    "matches": 5
  },
  "aggregated": { /* BalanceAggregation */ },
  "values": [
    { /* ProductBalance */ }
  ]
}
```

HTTP status: `200 OK`, `404 Not Found`, `422 Unprocessable Entity`

---

## Objects

### ProductBalance

| Field | Type | Description |
|-------|------|-------------|
| `productId` | String | Product UUID |
| `productType` | String | `ACCOUNT`, `CARD`, `DEPOT`, `LOAN`, `SAVINGS` |
| `targetClientId` | String | Customer connection UUID |
| `clientConnectionType` | String | `CURRENT_CLIENT` or `OTHER_COMDIRECT` |
| `balance` | AccountBalance \| CardBalance \| DepotAggregation \| InstallmentLoanBalance \| FixedTermSavings | Balance object matching productType |

**Product Types:**

| Value | Products Included |
|-------|-------------------|
| `ACCOUNT` | Girokonto, Verrechnungskonto, Tagesgeld-Plus, Fremdwährungskonto, CFD-Konto, Wertpapierkredit, Options- & Futures-Konto |
| `CARD` | Visa-Karte |
| `DEPOT` | Wertpapierdepot |
| `LOAN` | Ratenkredit |
| `SAVINGS` | Termingeld |

---

### BalanceAggregation

| Field | Type | Description |
|-------|------|-------------|
| `balanceEUR` | AmountValue | Aggregated balance across all returned products |
| `availableCashAmountEUR` | AmountValue | Available capital across all returned products |

---

### CardBalance

| Field | Type | Description |
|-------|------|-------------|
| `cardId` | String | Card UUID |
| `card` | Card + NULL | Card master data |
| `balance` | AmountValue | Current balance |
| `availableCashAmount` | AmountValue | Available amount (balance + limit - reserved) |

---

### Card

| Field | Type | Description |
|-------|------|-------------|
| `cardId` | String(≤40) | Card UUID |
| `clientId` | String | Customer UUID |
| `participantId` | String | Contract UUID |
| `cardType` | EnumText | Card type (see table below) |
| `holderName` | String | Card holder name |
| `settlementAccountId` | String | Default settlement account (Girokonto) UUID |
| `cardDisplayId` | String(16) | Partially anonymized card number (e.g. `XXXX XXXX XXXX 1234`) |
| `cardValidity` | String + NULL | Card expiry `MM/JJ` |
| `cardImage` | VisaCardImage | Card design |
| `primaryAccountNumberSuffix` | String | Last 4 digits of card number |
| `cardLimit` | AmountValue + NULL | Card spending limit |
| `status` | String | `ACTIVE`, `INACTIVE`, `IN_CHANGE`, `UNKNOWN` |

**Card Types:**

| Key | Display Text |
|-----|-------------|
| `AMERICAN_EXPRESS` | AMEX |
| `MASTERCARD` | Mastercard |
| `VISA_PREPAID` | Visa-Karte (Prepaid-Kreditkarte) |
| `VISA_CREDIT` | Visa-Karte (Kreditkarte) |
| `UNKNOWN` | Unbekannt |

---

### VisaCardImage

| Field | Type | Description |
|-------|------|-------------|
| `visaCardImageId` | String | Card design ID |
| `imageDescription` | String | Card design name |
| `imageBaseFilename` | String | Base filename for image variants (append postfix for size variant) |

---

### InstallmentLoanBalance

| Field | Type | Description |
|-------|------|-------------|
| `installmentLoanId` | String | Installment loan UUID |
| `installmentLoan` | InstallmentLoan + NULL | Loan master data |
| `balance` | AmountValue | Current outstanding balance in EUR (incl. insurance premium if financed + accrued interest) |

---

### InstallmentLoan

| Field | Type | Description |
|-------|------|-------------|
| `installmentLoanId` | String | Internal loan UUID |
| `productDisplayId` | String | 10-digit loan number |
| `creditAmount` | AmountValue | Approved credit amount (incl. insurance + interest) |
| `netCreditAmount` | AmountValue | Net approved amount (before interest/insurance) |
| `paidOutAmount` | AmountValue | Actually disbursed amount |
| `installmentAmount` | AmountValue | Monthly installment amount |
| `contractPeriodInMonths` | Integer | Loan term in months |
| `effectiveInterest` | PercentageString | Effective annual interest rate |
| `nominalInterest` | PercentageString | Nominal interest rate |
| `contractConclusionDate` | DateString | Contract start date |

---

### FixedTermSavings

| Field | Type | Description |
|-------|------|-------------|
| `fixedTermSavingsId` | String | Fixed-term savings UUID |
| `savingsAmount` | AmountValue | Invested amount |
| `interestRate` | AmountValue | Interest rate |
| `fixedTermSavingsType` | FixedTermSavingsType | `SHORT_TERM` or `LONG_TERM` |
| `fixedTermSavingsDisplayName` | String | Account display name |
| `contractPeriodInMonths` | Integer | Term in months |
| `creationDate` | DateString | Investment start date |
| `expirationDate` | DateString | Maturity date |
| `prolongationAmount` | AmountValue | Amount to be reinvested at maturity (may differ from original) |
| `extendable` | Boolean | `true` if the investment can be rolled over |

**FixedTermSavings Types:**

| Value | German | Term |
|-------|--------|------|
| `SHORT_TERM` | Festgeldkonto | 1–3 months |
| `LONG_TERM` | Laufzeitkonto | 120 months |

# comdirect REST API — Resource ACCOUNT

Access account balances and transaction history.

**Required scope:** `BANKING_RO`

---

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/banking/clients/{clientId}/v2/accounts/balances` | All account balances |
| GET | `/banking/v2/accounts/{accountId}/balances` | Single account balance |
| GET | `/banking/v1/accounts/{accountId}/transactions` | Account transactions |

> `accountId` (UUID) can be retrieved from the all-balances endpoint.

---

## GET /banking/clients/{clientId}/v2/accounts/balances

Retrieve balances for all accounts.

**Path parameters:**
- `clientId`: literal `"user"` (or customer UUID)

**Query parameters:**
- `without-attr=account`: suppress Account master data in response

**Response:**
```json
{
  "paging": {
    "index": 0,
    "matches": 3
  },
  "values": [
    { /* AccountBalance */ },
    ...
  ]
}
```

HTTP status: `200 OK`, `404 Not Found`, `422 Unprocessable Entity`

---

## GET /banking/v2/accounts/{accountId}/balances

Retrieve balance for a single account.

**Path parameters:**
- `accountId`: account UUID

**Query parameters:**
- `without-attr=account`: suppress Account master data

**Response:** Single `AccountBalance` object (with nested Account data by default).

HTTP status: `200 OK`, `404 Not Found`, `422 Unprocessable Entity`

---

## GET /banking/v1/accounts/{accountId}/transactions

Retrieve transaction list for a specific account.

**Path parameters:**
- `accountId`: account UUID

**Query parameters:**

| Parameter | Type | Default | Values | Description |
|-----------|------|---------|--------|-------------|
| `transactionState` | String | `BOTH` | `BOOKED`, `NOTBOOKED`, `BOTH` | Filter by booking status |
| `transactionDirection` | String | `CREDIT_AND_DEBIT` | `CREDIT`, `DEBIT`, `CREDIT_AND_DEBIT` | Filter by direction |
| `paging-first` | Integer | 0 | — | Index of first result |
| `with-attr` | String | — | `account` | Include Account master data |

**Response:**
```json
{
  "paging": {
    "index": 0,
    "matches": 150
  },
  "aggregated": { /* AccountTransactionAggregate */ },
  "values": [
    { /* AccountTransaction */ },
    ...
  ]
}
```

HTTP status: `200 OK`, `404 Not Found`

---

## Objects

### Account

| Field | Type | Description |
|-------|------|-------------|
| `accountId` | String(≤40) | Account UUID |
| `accountDisplayId` | String(12) | Account number (display) |
| `currency` | CurrencyString | Account currency |
| `clientId` | String(≤40) | Customer number |
| `accountType` | EnumText | Account type (see table below) |
| `iban` | String(≤34) + NULL | IBAN if available |
| `creditLimit` | AmountValue + NULL | Credit line if available |

**Account Type Keys:**

| Key | English Value | German |
|-----|---------------|--------|
| `FX` | Foreign Currency Account | Fremdwährungskonto |
| `OF` | Options & Futures Trading Account | Options- & Futures-Konto |
| `CA` | Checking Account | Girokonto |
| `DAS` | Direct Access Savings-Plus Account | Tagesgeld-Plus Konto |
| `CFD` | Contract for Difference Account | Contract for Difference Konto |
| `SA` | Settlement Account | Tagesgeld-/Verrechnungskonto |
| `LLA` | Lombard Loan Account | Wertpapier-Kreditkonto |

---

### AccountBalance

| Field | Type | Description |
|-------|------|-------------|
| `account` | Account | Account master data |
| `accountId` | String(≤40) | Account UUID |
| `balance` | AmountValue | Current balance |
| `balanceEUR` | AmountValue | Current balance in EUR |
| `availableCashAmount` | AmountValue | Available amount (balance + credit limit - reserved) |
| `availableCashAmountEUR` | AmountValue | Available amount in EUR |

---

### AccountTransaction

| Field | Type | Description |
|-------|------|-------------|
| `bookingStatus` | String | `BOOKED` or `NOTBOOKED` |
| `bookingDate` | DateString + NULL | Booking date `YYYY-MM-DD` |
| `amount` | AmountValue | Transaction amount |
| `remitter` | AccountInformation | Originator (holder name, IBAN, BIC) |
| `debtor` | AccountInformation | Debtor (holder name, IBAN, BIC) |
| `creditor` | AccountInformation | Creditor (holder name, IBAN, BIC) |
| `reference` | String | Unique reference number |
| `endToEndReference` | String | End-to-end reference (direct debit) |
| `valutaDate` | String | Value date (may be non-calendar date like 30.02) |
| `directDebitCreditorId` | String | Creditor ID for direct debits |
| `directDebitMandateId` | String | Mandate reference for direct debits |
| `transactionType` | EnumText | Transaction category (see table below) |
| `remittanceInfo` | String | Booking text (35-char lines, prepended with line numbers for booked transactions) |
| `newTransaction` | Boolean | `true` if not yet seen by customer in web |

**Transaction Type Keys:**

| Key (German) | English |
|--------------|---------|
| Sparplan | Saving Plan |
| Wertpapier | Securities |
| Geldanlage | Investment Saving |
| Bankgebühren | Bank fees |
| Sonstiges | Miscellaneous |
| Bar | Cash |
| Zinsen / Dividenden | Interest / Dividends |
| Devisen | Currency Exchange |
| Storno | Cancellation |
| Scheck | Cheque |
| Lastschrift | Direct Debit |
| Überweisung | Transfer |
| Kartenverfügung | Card transaction |
| Sorten (Kasse) | Foreign Currency exchange |
| Geldautomat | ATM Withdrawal |
| Geldanlage | Savings |
| Dauerauftrag | Standing Order |

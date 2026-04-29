# comdirect REST API — Resource DOCUMENTS

Access PostBox documents (statements, notifications, etc.).

**Required scope:** `MESSAGES_RO`

---

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/messages/clients/{clientId}/v2/documents` | List PostBox documents |
| GET | `/messages/v2/documents/{documentId}` | Download a document |
| GET | `/messages/v2/documents/{documentId}/predocument` | Get pre-document page (if available) |

---

## GET /messages/clients/{clientId}/v2/documents

Retrieve list of PostBox documents.

**Path parameters:**
- `clientId`: literal `"user"` or client UUID

**Query parameters:**

| Parameter | Type | Default | Max | Description |
|-----------|------|---------|-----|-------------|
| `paging-first` | Integer | 0 | — | Index of first result |
| `paging-count` | Integer | 20 | 1000 | Max results to return |

**Response:**
```json
{
  "paging": {
    "index": 0,
    "matches": 42
  },
  "values": [
    { /* Document */ }
  ]
}
```

HTTP status: `200 OK`, `404 Not Found`, `422 Unprocessable Entity`

---

## GET /messages/v2/documents/{documentId}

Download a single document.

**Path parameters:**
- `documentId`: document UUID

> **Important:** Reading an unread document marks it as read.

**Request header — must set Accept to match document's mimeType:**
```http
Accept: application/pdf
```
or
```http
Accept: text/html
```

**Response:** Binary content (PDF or HTML) with matching `Content-Type`.

HTTP status: `200 OK`, `404 Not Found`, `406 Not Acceptable` (Accept header mismatch)

---

## GET /messages/v2/documents/{documentId}/predocument

Get the pre-document page for a document (HTML format only, if available).

**Path parameters:**
- `documentId`: document UUID

**Request header:**
```http
Accept: text/html
```

**Response:** HTML content. Only available when `Document.documentMetadata.predocumentExists = true`.

HTTP status: `200 OK`, `404 Not Found`

---

## Objects

### Document

| Field | Type | Description |
|-------|------|-------------|
| `documentId` | String | Document UUID |
| `name` | String | Subject/title of the document |
| `dateCreation` | DateString | Creation/receipt date |
| `mimeType` | String | MIME type: `application/pdf` or `text/html` |
| `deleteable` | Boolean | `true` if document can be deleted |
| `advertisement` | Boolean | `true` if document is advertising |
| `documentMetadata` | DocumentMetadata | Document metadata |

### DocumentMetadata

| Field | Type | Description |
|-------|------|-------------|
| `archived` | Boolean | `true` if document has been moved to archive |
| `dateRead` | DateString + NULL | Date when document was read |
| `alreadyRead` | Boolean | `true` if document has been read |
| `predocumentExists` | Boolean | `true` if an HTML pre-document page is available |

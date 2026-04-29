# Bank Worker

Liest stündlich neue Überweisungen vom Comdirect-Konto und verarbeitet sie.

## Voraussetzungen

- Python 3.11+
- Comdirect Developer-Account + registrierte App → [https://developer.comdirect.de](https://developer.comdirect.de)
- Aus der registrierten App: `Client ID` und `Client Secret`

## Client ID und Client Secret besorgen

1. Gehe auf [https://developer.comdirect.de](https://developer.comdirect.de) und registriere dich
2. Nach Login: **"My Apps"** → **"Create App"**
3. App-Name und Beschreibung eingeben (z.B. "Ticket Worker")
4. Als **Redirect URI** kannst du `http://localhost` eintragen — wird für diesen Worker nicht aktiv genutzt
5. Nach dem Erstellen siehst du `Client ID` und `Client Secret` in den App-Details

> Die App muss mit deinem echten Comdirect-Kundenkonto verknüpft sein — du loggst dich in `setup.py` mit deiner normalen Kundennummer und PIN ein.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate # fish shell: source venv/bin/activate.fish
pip install -r requirements.txt
```

Lege eine `.env`-Datei an (wird nicht committet):

```env
COMDIRECT_CLIENT_ID=deine_client_id
COMDIRECT_CLIENT_SECRET=dein_client_secret
COMDIRECT_USERNAME=deine_kundennummer
COMDIRECT_PIN=deine_pin
```

## Einmalig: Authentifizierung mit PushTAN

Muss einmalig ausgeführt werden — danach läuft der Worker automatisch.

```fish
# Fish Shell
env (cat .env | grep -v '^#') python setup.py

# Bash/Zsh
export $(cat .env | xargs) && python setup.py
```

Ablauf:
1. Script loggt sich ein
2. PushTAN-Anfrage erscheint in der Comdirect App → bestätigen
3. `tokens.json` wird gespeichert

> `tokens.json` und `.env` nie committen — stehen in `.gitignore`

---

## Lokal testen

### 1. Einmalig ausführen

```fish
# Fish Shell
env (cat .env | grep -v '^#') python main.py

# Bash/Zsh
export $(cat .env | xargs) && python main.py
```

Ausgabe erscheint im Terminal + in `worker.log`.

### 2. Transaktionen simulieren (ohne echte API)

Für schnelle Tests ohne Bank-API: `client.py` temporär mocken.

Erstelle `mock_run.py`:

```python
from unittest.mock import patch, MagicMock
from main import handle_transaction

fake_tx = {
    "transactionId": "TEST-001",
    "remittanceInfo": "A1B2C3D4",   # simulierter Ticket-Code
    "amount": {"value": "6.00", "unit": "EUR"},
    "debtor": {"holderName": "Max Mustermann"},
}

handle_transaction(fake_tx)
```

```bash
python mock_run.py
```

So kannst du `handle_transaction()` entwickeln ohne echte Überweisungen.

### 3. Token abgelaufen simulieren

```bash
echo '{"access_token":"invalid","refresh_token":"invalid","session_id":"test"}' > tokens.json
python main.py
# → Fehler: "Token abgelaufen — bitte setup.py erneut ausführen"
```

---

## Server-Deployment

### 1. Code auf Server kopieren

```bash
rsync -av --exclude='tokens.json' --exclude='.env' --exclude='__pycache__' \
  ./bank-worker/ user@server:/opt/bank-worker/
```

### 2. Auf dem Server einrichten

```bash
ssh user@server
cd /opt/bank-worker
pip install -r requirements.txt

# .env anlegen
nano .env  # Werte eintragen

# Einmalig authentifizieren (PushTAN nötig)
export $(cat .env | xargs) && python setup.py  # Bash
```

### 3. Cron-Job einrichten

```bash
crontab -e
```

```cron
0 * * * * cd /opt/bank-worker && export $(cat .env | xargs) && python main.py >> worker.log 2>&1
```

### 4. Logs prüfen

```bash
tail -f /opt/bank-worker/worker.log
```

---

## Token abgelaufen (Fehlerfall)

Wenn `worker.log` meldet: `Token abgelaufen — bitte setup.py erneut ausführen`

```bash
ssh user@server
cd /opt/bank-worker
export $(cat .env | xargs) && python setup.py   # PushTAN erneut bestätigen
```

---

## Dateien

| Datei | Beschreibung |
|---|---|
| `client.py` | Comdirect API Client |
| `setup.py` | Einmalige Authentifizierung |
| `main.py` | Cron-Job Worker |
| `tokens.json` | Gespeicherte Tokens (auto-generiert) |
| `seen_transactions.json` | Bereits verarbeitete Transaktions-IDs |
| `worker.log` | Log-Ausgabe |
| `.env` | Zugangsdaten (nicht committen) |

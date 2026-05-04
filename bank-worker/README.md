# Bank Worker

Läuft dauerhaft und prüft alle 1 Minute neue Überweisungen auf dem Comdirect-Konto. Bei einer passenden Transaktion wird der Zahlungsstatus automatisch im Google Sheet aktualisiert.

## Voraussetzungen

- Python 3.11+
- Comdirect Developer-Account + registrierte App → [https://developer.comdirect.de](https://developer.comdirect.de)
- Google Service Account mit Zugriff auf das Sheet (siehe unten)

## Setup

### 1. Virtuelle Umgebung & Dependencies

```bash
python3 -m venv venv
source venv/bin/activate       # Bash/Zsh
source venv/bin/activate.fish  # Fish Shell
pip install -r requirements.txt
```

### 2. Konfiguration

```bash
cp example.env .env
# .env ausfüllen — Kommentare in der Datei erklären woher die Werte kommen
```

### 3. Google Service Account

1. [Google Cloud Console](https://console.cloud.google.com) → Projekt auswählen oder neu anlegen
2. **APIs & Dienste → Credentials → Create Credentials → Service Account**
3. Service Account erstellen, dann unter **Keys → Add Key → JSON** herunterladen
4. Die heruntergeladene Datei als `service_account.json` in diesen Ordner legen
5. Das Google Sheet mit der E-Mail-Adresse des Service Accounts teilen (Editor-Rechte)

> `service_account.json` und `.env` nie committen — stehen in `.gitignore`

## Authentifizierung via Telegram Bot

Auth wird über den Telegram Bot gesteuert — kein SSH nötig, PushTAN kommt nur wenn du es explizit auslöst.

### Bot-Commands

| Command | Funktion |
|---|---|
| `/auth` | Phase 1: Login + PushTAN auslösen |
| `/confirm` | Phase 2: Session aktivieren + `tokens.json` speichern |
| `/start_worker` | `systemctl start bank-worker` |
| `/status` | `systemctl status bank-worker` |
| `/help` | Command-Übersicht |

### Auth-Flow

1. `/auth` im Telegram-Chat senden
2. PushTAN erscheint in der Comdirect App → bestätigen
3. `/confirm` senden → `tokens.json` gespeichert
4. `/start_worker` senden

Bei abgelaufenem Token beendet sich `main.py` mit Exit-Code 42 (kein Neustart via systemd) und sendet eine Telegram-Nachricht. Dann wieder ab Schritt 1.

### Erstmalig lokal ausführen (ohne systemd)

```bash
# Bash/Zsh
export $(cat .env | xargs) && python auth_setup.py

# Fish Shell
env (cat .env | grep -v '^#') python auth_setup.py
```

## Deployment (systemd)

```bash
# Services einrichten
sudo cp setup/bank-worker.service /etc/systemd/system/
sudo cp setup/bank-worker-bot.service /etc/systemd/system/
sudo systemctl daemon-reload

# Bot immer starten (läuft dauerhaft)
sudo systemctl enable --now bank-worker-bot

# Worker erst nach Auth via Bot starten (/start_worker)
sudo systemctl enable bank-worker
```

## Worker lokal starten

```bash
# Bash/Zsh
export $(cat .env | xargs) && python main.py

# Fish Shell
env (cat .env | grep -v '^#') python main.py
```

Logs erscheinen im Terminal, in `worker.log` und `bot.log`.

## Lokale Tests ohne echte Bank-API

Erstelle `mock_run.py`:

```python
from unittest.mock import MagicMock
from main import handle_transaction

fake_tx = {
    "reference": "TEST-001",
    "remittanceInfo": "01NR69QDZ5                          ",
    "amount": {"value": "6.00", "unit": "EUR"},
    "remitter": {"holderName": "Max Mustermann"},
}

sheet = MagicMock()
handle_transaction(fake_tx, sheet)
```

```bash
python mock_run.py
```

## Dateien

| Datei | Beschreibung |
|---|---|
| `client.py` | Comdirect API Client |
| `auth_setup.py` | Einmalige Authentifizierung lokal (PushTAN) |
| `main.py` | Dauerhaft laufender Worker |
| `telegram_bot.py` | Telegram Bot (Auth-Control + Worker-Steuerung) |
| `sheet.py` | Google Sheets Integration |
| `setup/bank-worker.service` | systemd Unit für den Worker |
| `setup/bank-worker-bot.service` | systemd Unit für den Telegram Bot |
| `tokens.json` | Gespeicherte Tokens (auto-generiert) |
| `seen_transactions.json` | Bereits verarbeitete Transaktions-IDs |
| `worker.log` | Log-Ausgabe Worker |
| `bot.log` | Log-Ausgabe Telegram Bot |
| `service_account.json` | Google Service Account Credentials (nicht committen) |
| `.env` | Zugangsdaten (nicht committen) |

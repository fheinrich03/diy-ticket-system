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

## Einmalig: Authentifizierung mit PushTAN

Muss einmalig ausgeführt werden, danach läuft der Worker automatisch weiter und erneuert Tokens selbstständig.

```bash
# Bash/Zsh
export $(cat .env | xargs) && python auth_setup.py

# Fish Shell
env (cat .env | grep -v '^#') python auth_setup.py
```

Ablauf:
1. Script loggt sich ein
2. PushTAN-Anfrage erscheint in der Comdirect App → bestätigen
3. Enter drücken → `tokens.json` wird gespeichert

> Bei abgelaufenem Refresh-Token startet `main.py` den Auth-Flow automatisch neu (PushTAN erneut nötig).

## Worker starten

```bash
# Bash/Zsh
export $(cat .env | xargs) && python main.py

# Fish Shell
env (cat .env | grep -v '^#') python main.py
```

Der Worker läuft dauerhaft und pollt alle 1 Minute. Logs erscheinen im Terminal und in `worker.log`.

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
| `auth_setup.py` | Einmalige Authentifizierung (PushTAN) |
| `main.py` | Dauerhaft laufender Worker |
| `sheet.py` | Google Sheets Integration |
| `tokens.json` | Gespeicherte Tokens (auto-generiert) |
| `seen_transactions.json` | Bereits verarbeitete Transaktions-IDs |
| `worker.log` | Log-Ausgabe |
| `service_account.json` | Google Service Account Credentials (nicht committen) |
| `.env` | Zugangsdaten (nicht committen) |

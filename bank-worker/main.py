"""
Bank-Worker: läuft dauerhaft, prüft alle 5 Minuten neue Überweisungen auf Comdirect.
Token wird alle 5 Minuten refresht (gültig: ~10–20 Min, Retry: 3×, Abstand: 1 Min).
Bei abgelaufenem Refresh-Token wird automatisch setup.py ausgeführt (PushTAN nötig).
"""

import json
import logging
import os
import sys
import time
from pathlib import Path

import gspread
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials

from client import ComdirectClient
from setup import run_setup

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(__file__).parent / "worker.log"),
    ],
)
log = logging.getLogger(__name__)

SEEN_FILE = Path(__file__).parent / "seen_transactions.json"
SHEET_COL_ANMELDECODE = 2   # B
SHEET_COL_BEZAHLT_EUR = 10  # J


def get_sheet() -> gspread.Worksheet:
    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_file(
        Path(__file__).parent / "service_account.json", scopes=scopes
    )
    gc = gspread.authorize(creds)
    sheet_id = os.environ["GOOGLE_SHEET_ID"]
    return gc.open_by_key(sheet_id).sheet1
POLL_INTERVAL = 1 * 60   # 5 Minuten
REFRESH_RETRIES = 3
REFRESH_RETRY_DELAY = 60  # 1 Minute zwischen Retries


def load_seen() -> set[str]:
    if not SEEN_FILE.exists():
        return set()
    return set(json.loads(SEEN_FILE.read_text()))


def save_seen(ids: set[str]) -> None:
    SEEN_FILE.write_text(json.dumps(list(ids)))


def parse_remittance_info(remittance_info: str) -> str:
    """Extract segment 01 content from structured remittanceInfo (DTAUS format).
    Segments are fixed 37 chars: 2-digit prefix + 35 chars content.
    e.g. '01NR69QDZ5                  02End-to-End-Ref.: ...' -> 'NR69QDZ5'
    Falls back to full string stripped if no segment 01 found."""
    import re
    match = re.search(r'(?:^|\s)01(.{35})', remittance_info)
    if match:
        return match.group(1).strip()
    return remittance_info.strip()


def handle_transaction(tx: dict) -> None:
    """Called once per new incoming transaction. Add your logic here."""
    amount          = tx.get("amount", {}).get("value", "?")
    currency        = tx.get("amount", {}).get("unit", "EUR")
    remitter        = (tx.get("remitter") or {}).get("holderName", "Unbekannt")
    remittance_raw  = tx.get("remittanceInfo", "")
    anmeldecode     = parse_remittance_info(remittance_raw) if remittance_raw else ""

    log.info(f"Neue Überweisung: {remitter} | {amount} {currency} | Anmeldecode: '{anmeldecode}'")

    if not anmeldecode:
        log.warning("Transaktion ohne Verwendungszweck — übersprungen")
        return

    try:
        sheet = get_sheet()
        codes = sheet.col_values(SHEET_COL_ANMELDECODE)  # alle Werte in Spalte B
        anmeldecode_upper = anmeldecode.upper()
        for row_idx, code in enumerate(codes, start=1):
            if code and str(code).strip().upper() == anmeldecode_upper:
                sheet.update_cell(row_idx, SHEET_COL_BEZAHLT_EUR, amount)
                log.info(f"Sheet aktualisiert: Zeile {row_idx} | bezahlt_eur={amount}")
                return
        log.warning(f"Kein Eintrag für Anmeldecode '{anmeldecode}' im Sheet gefunden")
    except Exception as e:
        log.error(f"Google Sheets Fehler: {e}")


def reauthenticate(client: ComdirectClient, client_id: str, client_secret: str) -> bool:
    """Führt vollständigen Auth-Flow (setup) durch und lädt neue Tokens in den Client."""
    log.info("Starte erneute Authentifizierung (PushTAN erforderlich) ...")
    try:
        new_client = run_setup(client_id, client_secret)
        client.access_token = new_client.access_token
        client.refresh_token = new_client.refresh_token
        client.session_id = new_client.session_id
        log.info("Erneute Authentifizierung erfolgreich")
        return True
    except Exception as e:
        log.error(f"Erneute Authentifizierung fehlgeschlagen: {e}")
        return False


def refresh_with_retry(client: ComdirectClient, client_id: str, client_secret: str) -> bool:
    """Versucht Token zu refreshen, 3 Retries mit 1 Min Abstand.
    Bei abgelaufenem Refresh-Token: automatisch setup/PushTAN-Flow."""
    for attempt in range(1, REFRESH_RETRIES + 1):
        try:
            if client.refresh():
                client.save_tokens()
                log.info("Token erfolgreich refresht")
                return True
            else:
                log.warning("Refresh-Token abgelaufen — starte automatische Neuanmeldung")
                return reauthenticate(client, client_id, client_secret)
        except Exception as e:
            log.warning(f"Refresh fehlgeschlagen (Versuch {attempt}/{REFRESH_RETRIES}): {e}")
            if attempt < REFRESH_RETRIES:
                log.info(f"Retry in {REFRESH_RETRY_DELAY}s ...")
                time.sleep(REFRESH_RETRY_DELAY)
    log.warning("Alle Refresh-Versuche fehlgeschlagen — starte automatische Neuanmeldung")
    return reauthenticate(client, client_id, client_secret)


def poll(client: ComdirectClient) -> None:
    """Einmaliger Poll: alle Konten abfragen, neue Transaktionen verarbeiten."""
    accounts = client.get_accounts()
    if not accounts:
        log.warning("Keine Konten gefunden")
        return

    seen = load_seen()
    new_seen = set(seen)

    for account in accounts:
        account_id = account["accountId"]
        iban       = account.get("iban", account_id)

        transactions = client.get_transactions(account_id, days_back=2)
        log.info(f"Konto {iban}: {len(transactions)} Transaktionen abgerufen")

        for tx in transactions:
            tx_id = tx.get("reference")
            if not tx_id or tx_id in seen:
                continue
            handle_transaction(tx)
            new_seen.add(tx_id)

    save_seen(new_seen)


def run() -> None:
    client_id     = os.environ.get("COMDIRECT_CLIENT_ID", "user")
    client_secret = os.environ.get("COMDIRECT_CLIENT_SECRET", "secret")

    client = ComdirectClient(client_id, client_secret)

    # Cold start: tokens.json fehlt oder Refresh schlägt sofort fehl → direkt setup
    if not client.load_tokens():
        log.info("Keine tokens.json — starte Authentifizierung (PushTAN erforderlich) ...")
        if not reauthenticate(client, client_id, client_secret):
            log.error("Authentifizierung fehlgeschlagen — Worker beendet sich")
            sys.exit(1)
    else:
        # tokens.json vorhanden — einmal ohne Retries testen ob noch gültig
        log.info("Teste gespeicherte Tokens ...")
        try:
            valid = client.refresh()
        except Exception:
            valid = False
        if valid:
            client.save_tokens()
            log.info("Tokens gültig")
        else:
            log.info("Tokens abgelaufen — starte Authentifizierung (PushTAN erforderlich) ...")
            if not reauthenticate(client, client_id, client_secret):
                log.error("Authentifizierung fehlgeschlagen — Worker beendet sich")
                sys.exit(1)

    log.info(f"Bank-Worker gestartet (Poll alle {POLL_INTERVAL // 60} Minuten)")

    while True:
        if not refresh_with_retry(client, client_id, client_secret):
            log.error("Authentifizierung fehlgeschlagen — Worker beendet sich")
            sys.exit(1)

        try:
            poll(client)
        except Exception as e:
            log.error(f"Fehler beim Poll: {e}")

        log.info(f"Warte {POLL_INTERVAL // 60} Minuten bis zum nächsten Poll ...")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run()

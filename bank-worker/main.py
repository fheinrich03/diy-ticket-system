"""
Bank-Worker: läuft dauerhaft, prüft alle 5 Minuten neue Überweisungen auf Comdirect.
Token wird alle 5 Minuten refresht (gültig: ~10–20 Min, Retry: 3×, Abstand: 1 Min).
Bei abgelaufenem Refresh-Token wird automatisch auth_setup.py ausgeführt (PushTAN nötig).
"""

import json
import logging
import os
import sys
import time
from pathlib import Path

import gspread
from dotenv import load_dotenv

from auth_setup import run_setup
from client import ComdirectClient
from sheet import SHEET_COL_ANMELDECODE, SHEET_COL_BEZAHLT_EUR, apply_payment_status, get_sheet

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(__file__).parent / "worker.log"),
    ],
)
log = logging.getLogger(__name__)

SEEN_FILE = Path(__file__).parent / "seen_transactions.json"

POLL_INTERVAL = 1 * 60   # 1 Minute
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


def handle_transaction(tx: dict, sheet: gspread.Worksheet) -> None:
    """Called once per new incoming transaction. Add your logic here."""
    amount          = tx.get("amount", {}).get("value", "?")
    currency        = tx.get("amount", {}).get("unit", "EUR")
    remitter        = (tx.get("remitter") or {}).get("holderName", "Unbekannt")
    remittance_raw  = tx.get("remittanceInfo", "")
    anmeldecode     = parse_remittance_info(remittance_raw) if remittance_raw else ""

    log.info(f"Überweisung: {remitter} | {amount} {currency} | remittanceInfo={remittance_raw!r} | Anmeldecode: '{anmeldecode}'")

    if not anmeldecode:
        log.warning("Transaktion ohne Verwendungszweck — übersprungen")
        return

    try:
        codes = sheet.col_values(SHEET_COL_ANMELDECODE)  # alle Werte in Spalte B
        anmeldecode_upper = anmeldecode.upper()
        for row_idx, code in enumerate(codes, start=1):
            if code and str(code).strip().upper() == anmeldecode_upper:
                sheet.update_cell(row_idx, SHEET_COL_BEZAHLT_EUR, amount)
                log.info(f"Sheet aktualisiert: Zeile {row_idx} | bezahlt_eur={amount}")
                apply_payment_status(sheet, row_idx, float(amount))
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

    sheet = get_sheet()

    for account in accounts:
        account_id = account["accountId"]
        iban       = account.get("iban", account_id)

        transactions = client.get_transactions(account_id, days_back=2)

        for tx in transactions:
            raw_ref = (tx.get("reference") or "").strip()
            if not raw_ref:
                # Bank liefert keinen reference — Fallback aus Betrag + remittanceInfo
                amount_val = tx.get("amount", {}).get("value", "")
                remittance = (tx.get("remittanceInfo") or "").strip()
                raw_ref = f"_fallback_{amount_val}_{remittance}"
                log.debug(f"Transaktion ohne reference, Fallback-Key: {raw_ref!r}")
            if raw_ref in seen:
                log.debug(f"Bereits gesehen, übersprungen: {raw_ref!r}")
                continue
            handle_transaction(tx, sheet)
            new_seen.add(raw_ref)

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
        try:
            valid = client.refresh()
        except Exception:
            valid = False
        if valid:
            client.save_tokens()
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

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run()

"""
Bank-Worker: läuft dauerhaft, prüft alle 5 Minuten neue Überweisungen auf Comdirect.
Token wird alle 5 Minuten refresht (gültig: ~10–20 Min, Retry: 3×, Abstand: 1 Min).
"""

import json
import logging
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

from client import ComdirectClient

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
POLL_INTERVAL = 5 * 60   # 5 Minuten
REFRESH_RETRIES = 3
REFRESH_RETRY_DELAY = 60  # 1 Minute zwischen Retries


def load_seen() -> set[str]:
    if not SEEN_FILE.exists():
        return set()
    return set(json.loads(SEEN_FILE.read_text()))


def save_seen(ids: set[str]) -> None:
    SEEN_FILE.write_text(json.dumps(list(ids)))


def handle_transaction(tx: dict) -> None:
    """Called once per new incoming transaction. Add your logic here."""
    reference = tx.get("reference", "")
    amount    = tx.get("amount", {}).get("value", "?")
    currency  = tx.get("amount", {}).get("unit", "EUR")
    name      = (tx.get("creditor") or {}).get("holderName") \
             or (tx.get("debtor") or {}).get("holderName", "Unbekannt")
    remitter  = (tx.get("remitter") or {}).get("holderName", "Unbekannt")

    log.info(f"Neue Überweisung: {name} | {amount} {currency} | Ref: {reference} | Remitter: {remitter}")

    # TODO: hier Ticket-Logik einhängen, z.B.:
    # - Verwendungszweck mit anmeldecode aus Google Sheets abgleichen
    # - Sheet via Google Sheets API als bezahlt markieren
    # - sendTicketEmail auslösen (z.B. via HTTP-Trigger)


def refresh_with_retry(client: ComdirectClient) -> bool:
    """Versucht Token zu refreshen, 3 Retries mit 1 Min Abstand."""
    for attempt in range(1, REFRESH_RETRIES + 1):
        try:
            if client.refresh():
                client.save_tokens()
                log.info("Token erfolgreich refresht")
                return True
            else:
                log.error("Refresh-Token abgelaufen — bitte setup.py erneut ausführen")
                return False
        except Exception as e:
            log.warning(f"Refresh fehlgeschlagen (Versuch {attempt}/{REFRESH_RETRIES}): {e}")
            if attempt < REFRESH_RETRIES:
                log.info(f"Retry in {REFRESH_RETRY_DELAY}s ...")
                time.sleep(REFRESH_RETRY_DELAY)
    log.error("Alle Refresh-Versuche fehlgeschlagen")
    return False


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
            tx_id = tx.get("transactionId")
            if not tx_id or tx_id in seen:
                continue
            handle_transaction(tx)
            new_seen.add(tx_id)

    save_seen(new_seen)


def run() -> None:
    client_id     = os.environ.get("COMDIRECT_CLIENT_ID", "user")
    client_secret = os.environ.get("COMDIRECT_CLIENT_SECRET", "secret")

    client = ComdirectClient(client_id, client_secret)

    if not client.load_tokens():
        log.error("tokens.json nicht gefunden — bitte setup.py ausführen")
        sys.exit(1)

    log.info(f"Bank-Worker gestartet (Poll alle {POLL_INTERVAL // 60} Minuten)")

    while True:
        if not refresh_with_retry(client):
            log.error("Token nicht erneuerbar — Worker beendet sich")
            sys.exit(1)

        try:
            poll(client)
        except Exception as e:
            log.error(f"Fehler beim Poll: {e}")

        log.info(f"Warte {POLL_INTERVAL // 60} Minuten bis zum nächsten Poll ...")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run()

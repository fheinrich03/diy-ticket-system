"""
Telegram Bot für Bank-Worker Auth-Control.
Läuft dauerhaft via bank-worker-bot.service.

Commands:
  /auth         — Phase 1: Login + PushTAN auslösen
  /confirm      — Phase 2: Session aktivieren + tokens.json speichern
  /start_worker — systemctl start bank-worker
  /status       — systemctl status bank-worker
  /help         — Command-Übersicht
"""

import logging
import os
import subprocess
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(__file__).parent / "bot.log"),
    ],
)
log = logging.getLogger(__name__)

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ALLOWED_CHAT_ID = int(os.environ["TELEGRAM_CHAT_ID"])
CLIENT_ID = os.environ.get("COMDIRECT_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("COMDIRECT_CLIENT_SECRET", "")

API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Auth state between /auth and /confirm
_auth_state: dict = {}  # keys: client, session_id, challenge_id


def send(chat_id: int, text: str) -> None:
    try:
        requests.post(f"{API}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=10)
    except Exception as e:
        log.error(f"Telegram send failed: {e}")


def handle_auth(chat_id: int) -> None:
    from client import ComdirectClient

    if _auth_state:
        send(chat_id, "Auth läuft bereits. /confirm zum Abschließen oder warte kurz.")
        return

    send(chat_id, "Starte Auth... PushTAN kommt gleich aufs Handy.")
    try:
        client = ComdirectClient(CLIENT_ID, CLIENT_SECRET)
        username = os.environ.get("COMDIRECT_USERNAME", "")
        pin = os.environ.get("COMDIRECT_PIN", "")
        client.login(username, pin)
        sess = client.get_session()
        session_id = sess["identifier"]
        challenge_id = client.request_tan(session_id)

        _auth_state["client"] = client
        _auth_state["session_id"] = session_id
        _auth_state["challenge_id"] = challenge_id

        send(chat_id, "PushTAN ausgelöst. In der Comdirect App bestaetigen, dann /confirm senden.")
    except Exception as e:
        _auth_state.clear()
        send(chat_id, f"Auth fehlgeschlagen: {e}")
        log.error(f"Auth phase 1 failed: {e}")


def handle_confirm(chat_id: int) -> None:
    if not _auth_state:
        send(chat_id, "Kein aktiver Auth-Vorgang. Erst /auth senden.")
        return

    try:
        client = _auth_state["client"]
        session_id = _auth_state["session_id"]
        challenge_id = _auth_state["challenge_id"]

        if not client.activate_session(session_id, challenge_id):
            send(chat_id, "Session-Aktivierung fehlgeschlagen. PushTAN bestaetigt?")
            return

        client.get_secondary_token()
        client.save_tokens()
        _auth_state.clear()

        send(chat_id, "Auth erfolgreich. tokens.json gespeichert. /start_worker zum Starten.")
        log.info("Auth confirmed via Telegram")
    except Exception as e:
        _auth_state.clear()
        send(chat_id, f"Confirm fehlgeschlagen: {e}")
        log.error(f"Auth phase 2 failed: {e}")


def handle_start_worker(chat_id: int) -> None:
    result = subprocess.run(
        ["systemctl", "start", "bank-worker"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        send(chat_id, "bank-worker gestartet.")
    else:
        send(chat_id, f"Fehler: {result.stderr.strip() or result.stdout.strip()}")


def handle_status(chat_id: int) -> None:
    result = subprocess.run(
        ["systemctl", "status", "bank-worker", "--no-pager", "-l"],
        capture_output=True, text=True
    )
    output = (result.stdout + result.stderr).strip()
    send(chat_id, output[:4000] if output else "Kein Output.")


def handle_help(chat_id: int) -> None:
    send(chat_id, (
        "Commands:\n"
        "/auth — PushTAN auslösen\n"
        "/confirm — Auth abschließen (nach PushTAN-Bestaetigung)\n"
        "/start_worker — bank-worker starten\n"
        "/status — bank-worker Status\n"
        "/help — diese Übersicht"
    ))


def handle_update(update: dict) -> None:
    msg = update.get("message") or update.get("edited_message")
    if not msg:
        return
    chat_id = msg.get("chat", {}).get("id")
    if chat_id != ALLOWED_CHAT_ID:
        return
    text = (msg.get("text") or "").strip()

    if text.startswith("/auth"):
        handle_auth(chat_id)
    elif text.startswith("/confirm"):
        handle_confirm(chat_id)
    elif text.startswith("/start_worker"):
        handle_start_worker(chat_id)
    elif text.startswith("/status"):
        handle_status(chat_id)
    elif text.startswith("/help"):
        handle_help(chat_id)


def run() -> None:
    log.info("Telegram bot started")
    offset = 0
    while True:
        try:
            resp = requests.get(
                f"{API}/getUpdates",
                params={"offset": offset, "timeout": 30},
                timeout=40,
            )
            data = resp.json()
            for update in data.get("result", []):
                offset = update["update_id"] + 1
                handle_update(update)
        except Exception as e:
            log.error(f"Polling error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    run()

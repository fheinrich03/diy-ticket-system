"""
Einmalig ausführen um tokens.json zu erstellen.
Danach läuft main.py automatisch ohne TAN.

    python auth_setup.py
"""

import os

from dotenv import load_dotenv

from client import ComdirectClient


def run_setup(
    client_id: str,
    client_secret: str,
    username: str | None = None,
    pin: str | None = None,
) -> ComdirectClient:
    """Führt den vollständigen Auth-Flow durch und speichert tokens.json.
    Blockiert bis PushTAN bestätigt und Enter gedrückt wurde.
    Gibt den authentifizierten Client zurück."""

    if username is None:
        username = os.environ.get("COMDIRECT_USERNAME") or input("Kundennummer: ")
    if pin is None:
        pin = os.environ.get("COMDIRECT_PIN") or input("PIN: ")

    client = ComdirectClient(client_id, client_secret)

    print("→ Login...")
    client.login(username, pin)

    print("→ Session abrufen...")
    sess = client.get_session()
    session_id = sess["identifier"]

    print("→ PushTAN wird ausgelöst — bitte in der Comdirect App bestätigen...")
    challenge_id = client.request_tan(session_id)

    # PATCH darf nur EINMAL aufgerufen werden, nachdem der User bestätigt hat.
    # Polling ist nicht möglich — jeder frühzeitige PATCH-Aufruf invalidiert die Challenge.
    input("  PushTAN in der App bestätigen, dann hier Enter drücken ...")

    if not client.activate_session(session_id, challenge_id):
        raise RuntimeError("Session-Aktivierung fehlgeschlagen (422) — TAN nicht bestätigt?")

    print("→ PushTAN bestätigt. Secondary Token holen...")
    client.get_secondary_token()

    client.save_tokens()
    print("✓ tokens.json gespeichert.")
    return client


if __name__ == "__main__":
    load_dotenv()
    client_id     = os.environ.get("COMDIRECT_CLIENT_ID", "user")
    client_secret = os.environ.get("COMDIRECT_CLIENT_SECRET", "secret")
    run_setup(client_id, client_secret)
    print("Fertig. main.py kann jetzt laufen.")

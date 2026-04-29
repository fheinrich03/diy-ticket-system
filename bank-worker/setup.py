"""
Einmalig ausführen um tokens.json zu erstellen.
Danach läuft main.py automatisch ohne TAN.

    python setup.py
"""

import os
from dotenv import load_dotenv
from client import ComdirectClient

load_dotenv()

username = os.environ.get("COMDIRECT_USERNAME") or input("Kundennummer: ")
pin      = os.environ.get("COMDIRECT_PIN")      or input("PIN: ")
client_id     = os.environ.get("COMDIRECT_CLIENT_ID", "user")
client_secret = os.environ.get("COMDIRECT_CLIENT_SECRET", "secret")

client = ComdirectClient(client_id, client_secret)

print("→ Login...")
client.login(username, pin)

print("→ Session abrufen...")
sess = client.get_session()
session_id = sess["identifier"]

print("→ PushTAN wird ausgelöst — bitte in der Comdirect App bestätigen...")
challenge_id = client.request_tan(session_id)

input("PushTAN in der App bestätigen, dann Enter drücken...")
client.activate_session(session_id, challenge_id)

print("→ Secondary Token holen...")
client.get_secondary_token()

client.save_tokens()
print("✓ tokens.json gespeichert. Cron-Job kann jetzt laufen.")

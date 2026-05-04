## Telegram Bot — Auth Control

### Problem / Kontext

- Auth-Token läuft nach ~1 Woche ab, trotz Refresh (Token hat maximale Laufzeit)
- Bei abgelaufenem Token versucht Worker automatisch Re-Auth → löst PushTAN-Aufträge aus
- Statt max. 3 kamen durchgängig PushTAN-Anfragen aufs Handy
- Sicherheitsproblem: man weiß nicht ob PushTAN wirklich von einem selbst kommt
- Ziel: PushTAN kommt **nur** wenn man es explizit auslöst

### Architektur

- `bank-worker-bot.service` — läuft immer, wartet auf Commands
- `bank-worker.service` — nur der Worker, kein Auto-Reauth mehr

### Flow

1. Worker: Token abgelaufen → Telegram-Nachricht "Auth erforderlich, /auth senden" → `sys.exit(1)`
2. Du: `/auth` im Telegram-Chat
3. Bot: startet `auth_setup.py` → PushTAN kommt aufs Handy
4. Du weißt: dieser PushTAN kommt von dir → bestätigen
5. Bot: "Auth erfolgreich ✓" → du sendest `/start_worker`
6. Bot: startet bank-worker via systemd

### Vorteile

- Kein SSH nötig für Re-Auth
- 100% sicher: PushTAN **nur** wenn du `/auth` schickst
- Keine unkontrollierten PushTAN-Floods mehr
- Einfache Commands statt Terminal

### Bot Commands

- `/auth` — startet Auth-Flow
- `/start_worker` — `systemctl start bank-worker`
- `/status` — `systemctl status bank-worker`

### Sicherheit

- Bot prüft bei jeder Nachricht die Chat-ID gegen `TELEGRAM_CHAT_ID` aus `.env`
- Nachrichten von fremden IDs werden stillschweigend ignoriert
- Gleiche Variable wie für Notifications — kein Extra-Setup nötig

```python
ALLOWED_CHAT_ID = int(os.environ.get("TELEGRAM_CHAT_ID"))

def handle_update(update):
    if update["message"]["chat"]["id"] != ALLOWED_CHAT_ID:
        return  # ignorieren
    # command verarbeiten
```

### Implementierung

~100 Zeilen Python mit raw `requests` + long polling, keine schwere Library nötig.

**Neue Dateien:**
- `telegram_bot.py` — Bot mit long polling + state machine für Auth
- `bank-worker-bot.service` — systemd unit, läuft immer

**Änderungen:**
- `main.py` — `reauthenticate()` entfernen, bei Auth-Fehler: Telegram notify + `sys.exit(42)`
- `bank-worker.service` — `RestartPreventExitStatus=42` hinzufügen (kein Loop bei Auth-Fehler)
- `example.env` — `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` hinzufügen

**Bot Commands:**
- `/auth` — Phase 1: Login + PushTAN auslösen
- `/confirm` — Phase 2: Session aktivieren + tokens.json speichern
- `/start_worker` — `systemctl start bank-worker`
- `/status` — `systemctl status bank-worker`
- `/help` — Command-Übersicht

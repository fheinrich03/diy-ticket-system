"""Comdirect REST API client."""

import json
import time
import uuid
from pathlib import Path

import requests

BASE_URL = "https://api.comdirect.de"
TOKEN_FILE = Path(__file__).parent / "tokens.json"


class ComdirectClient:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.session = requests.Session()
        self.access_token: str | None = None
        self.refresh_token: str | None = None
        self.session_id: str = str(uuid.uuid4())
        self.request_id: str = ""

    # ─── Auth ──────────────────────────────────────────────────────────────

    def _next_request_id(self) -> str:
        self.request_id = str(int(time.time() * 1000))[-9:]
        return self.request_id

    def _auth_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "x-http-request-info": json.dumps({
                "clientRequestId": {
                    "sessionId": self.session_id,
                    "requestId": self._next_request_id(),
                }
            }),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def login(self, username: str, pin: str) -> dict:
        """Step 1: password grant — returns access token (session not yet validated)."""
        resp = self.session.post(
            f"{BASE_URL}/oauth/token",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "password",
                "username": username,
                "password": pin,
            },
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        return data

    def get_session(self) -> dict:
        """Step 2: fetch session info needed for TAN validation."""
        resp = self.session.get(
            f"{BASE_URL}/api/session/clients/user/v1/sessions",
            headers=self._auth_headers(),
        )
        resp.raise_for_status()
        sessions = resp.json()
        return sessions[0] if sessions else {}

    def request_tan(self, session_id: str) -> str:
        """Step 3: trigger P_TAN_PUSH on phone. Returns challenge id from x-once-authentication-info."""
        headers = self._auth_headers()
        headers["x-once-authentication-info"] = json.dumps({"typ": "P_TAN_PUSH"})
        resp = self.session.post(
            f"{BASE_URL}/api/session/clients/user/v1/sessions/{session_id}/validate",
            json={"identifier": session_id, "sessionTanActive": True, "activated2FA": True},
            headers=headers,
        )
        resp.raise_for_status()
        auth_info_raw = resp.headers.get("x-once-authentication-info", "{}")
        challenge_id = json.loads(auth_info_raw).get("id", "")
        if not challenge_id:
            raise ValueError(f"Kein challenge_id in x-once-authentication-info: {auth_info_raw}")
        return challenge_id

    def activate_session(self, session_id: str, challenge_id: str, tan: str = "") -> bool:
        """Step 4: confirm TAN and activate session. tan is empty for PushTAN.
        Returns False if PushTAN not yet confirmed (422), raises on other errors."""
        headers = self._auth_headers()
        headers["x-once-authentication-info"] = json.dumps({"id": challenge_id})
        if tan:
            headers["x-once-authentication"] = tan
        resp = self.session.patch(
            f"{BASE_URL}/api/session/clients/user/v1/sessions/{session_id}",
            json={"identifier": session_id, "sessionTanActive": True, "activated2FA": True},
            headers=headers,
        )
        if resp.status_code == 422:
            return False
        resp.raise_for_status()
        return True

    def get_secondary_token(self) -> None:
        """Step 5: exchange for long-lived secondary token."""
        resp = self.session.post(
            f"{BASE_URL}/oauth/token",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "cd_secondary",
                "token": self.access_token,
            },
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]

    def refresh(self) -> bool:
        """Refresh access token using stored refresh token. Returns False if expired."""
        resp = self.session.post(
            f"{BASE_URL}/oauth/token",
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
            },
            headers={"Accept": "application/json"},
        )
        if resp.status_code in (400, 401):
            return False
        resp.raise_for_status()
        data = resp.json()
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        return True

    def revoke(self) -> None:
        self.session.delete(
            f"{BASE_URL}/oauth/revoke",
            headers=self._auth_headers(),
        )

    # ─── Token persistence ─────────────────────────────────────────────────

    def save_tokens(self) -> None:
        TOKEN_FILE.write_text(json.dumps({
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "session_id": self.session_id,
        }))

    def load_tokens(self) -> bool:
        if not TOKEN_FILE.exists():
            return False
        data = json.loads(TOKEN_FILE.read_text())
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]
        self.session_id = data["session_id"]
        return True

    # ─── Banking ───────────────────────────────────────────────────────────

    def get_accounts(self) -> list[dict]:
        resp = self.session.get(
            f"{BASE_URL}/api/banking/clients/user/v2/accounts/balances",
            headers=self._auth_headers(),
        )
        resp.raise_for_status()
        return resp.json().get("values", [])

    def get_transactions(self, account_id: str, days_back: int = 1) -> list[dict]:
        """Fetch transactions for the last `days_back` days."""
        from datetime import date, timedelta
        date_from = (date.today() - timedelta(days=days_back)).isoformat()
        resp = self.session.get(
            f"{BASE_URL}/api/banking/v1/accounts/{account_id}/transactions",
            params={"min-bookingDate": date_from},
            headers=self._auth_headers(),
        )
        resp.raise_for_status()
        return resp.json().get("values", [])

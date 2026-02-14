"""OAuth2 flow for Strava: browser-based authorization + token management."""

from __future__ import annotations

import asyncio
import hashlib
import secrets
import sqlite3
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
from typing import Any
from urllib.parse import parse_qs, urlparse

import httpx

STRAVA_AUTH_URL = "https://www.strava.com/oauth/authorize"
STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
CALLBACK_PORT = 5678
REDIRECT_URI = f"http://localhost:{CALLBACK_PORT}/callback"
SCOPES = "read,activity:read_all,profile:read_all"


class TokenStore:
    """SQLite-backed storage for OAuth tokens."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._ensure_table()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def _ensure_table(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tokens (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    access_token TEXT NOT NULL,
                    refresh_token TEXT NOT NULL,
                    expires_at INTEGER NOT NULL,
                    athlete_id INTEGER
                )
            """)

    def save(self, access_token: str, refresh_token: str, expires_at: int, athlete_id: int | None = None) -> None:
        with self._connect() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO tokens (id, access_token, refresh_token, expires_at, athlete_id)
                   VALUES (1, ?, ?, ?, ?)""",
                (access_token, refresh_token, expires_at, athlete_id),
            )

    def load(self) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT access_token, refresh_token, expires_at, athlete_id FROM tokens WHERE id = 1").fetchone()
        if row is None:
            return None
        return {
            "access_token": row[0],
            "refresh_token": row[1],
            "expires_at": row[2],
            "athlete_id": row[3],
        }

    def clear(self) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM tokens")


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler that captures the OAuth callback code."""

    authorization_code: str | None = None
    state_received: str | None = None

    def do_GET(self, /) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)

        if parsed.path == "/callback" and "code" in params:
            OAuthCallbackHandler.authorization_code = params["code"][0]
            OAuthCallbackHandler.state_received = params.get("state", [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h2>Authorization successful!</h2><p>You can close this tab.</p></body></html>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"Authorization failed.")

    def log_message(self, format: str, /, *args: Any) -> None:  # noqa: A002
        pass  # Suppress default logging


async def exchange_code(client_id: str, client_secret: str, code: str) -> dict[str, Any]:
    """Exchange authorization code for tokens."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            STRAVA_TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
            },
        )
        resp.raise_for_status()
        return resp.json()


async def refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> dict[str, Any]:
    """Refresh an expired access token."""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            STRAVA_TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
        resp.raise_for_status()
        return resp.json()


async def run_oauth_flow(client_id: str, client_secret: str) -> dict[str, Any]:
    """Run the full OAuth flow: open browser, wait for callback, exchange code."""
    state = hashlib.sha256(secrets.token_bytes(32)).hexdigest()[:16]

    OAuthCallbackHandler.authorization_code = None
    OAuthCallbackHandler.state_received = None

    server = HTTPServer(("127.0.0.1", CALLBACK_PORT), OAuthCallbackHandler)
    thread = Thread(target=server.handle_request, daemon=True)
    thread.start()

    auth_url = (
        f"{STRAVA_AUTH_URL}"
        f"?client_id={client_id}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={SCOPES}"
        f"&state={state}"
    )
    webbrowser.open(auth_url)

    # Wait for the callback (up to 120 seconds)
    for _ in range(240):
        if OAuthCallbackHandler.authorization_code is not None:
            break
        await asyncio.sleep(0.5)

    server.server_close()

    code = OAuthCallbackHandler.authorization_code
    if code is None:
        msg = "OAuth callback timed out — no authorization code received."
        raise TimeoutError(msg)

    if OAuthCallbackHandler.state_received != state:
        msg = "OAuth state mismatch — possible CSRF attack."
        raise ValueError(msg)

    return await exchange_code(client_id, client_secret, code)

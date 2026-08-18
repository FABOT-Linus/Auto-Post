#!/usr/bin/env python3
"""
LinkedIn OAuth 2.0 Authorization Helper

Runs a small local web server, opens your browser to LinkedIn's auth page,
catches the callback, and exchanges the authorization code for
access + refresh tokens.

PREREQUISITE:
  1. Go to https://www.linkedin.com/developers/ → your app
  2. Under "Auth" tab, add this redirect URL:
       http://localhost:8080/callback
  3. Make sure these products are added: "Sign In with LinkedIn" and "Share on LinkedIn"

USAGE:
  python3 linkedin_auth.py

  Then copy the printed tokens into your .env file.
"""

import os
import sys
import json
import webbrowser
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

import requests

# ─── Config ───────────────────────────────────────────────
CLIENT_ID = os.getenv("LINKEDIN_CLIENT_ID")
# CLIENT_SECRET should be set via env var or pasted at runtime
REDIRECT_URI = "http://localhost:8080/callback"
PORT = 8080
SCOPES = "openid profile w_member_social"

AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
USERINFO_URL = "https://api.linkedin.com/v2/userinfo"


class CallbackHandler(BaseHTTPRequestHandler):
    """Handles the OAuth callback from LinkedIn."""

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)

        if "error" in params:
            error = params["error"][0]
            error_desc = params.get("error_description", [""])[0]
            self._send_html(
                f"<h2>❌ Authorization failed</h2><p>{error}</p><p>{error_desc}</p>"
            )
            print(f"\n❌ Authorization failed: {error} — {error_desc}")
            self.server.auth_code = None
            return

        if "code" in params:
            code = params["code"][0]
            self._send_html(
                "<h2>✅ Authorization successful!</h2>"
                "<p>You can close this tab and return to your terminal.</p>"
            )
            print("\n✅ Got authorization code!")
            self.server.auth_code = code
            return

        self._send_html("<h2>Waiting for authorization...</h2>")

    def _send_html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(html.encode())

    def log_message(self, format, *args):
        pass  # silence default logging


def build_auth_url(client_id=None):
    if client_id is None:
        client_id = CLIENT_ID
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPES,
    }
    return f"{AUTH_URL}?{urllib.parse.urlencode(params)}"


def exchange_code(code, client_secret, client_id=None):
    """Exchange the auth code for access + refresh tokens."""
    if client_id is None:
        client_id = CLIENT_ID
    resp = requests.post(
        TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": REDIRECT_URI,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        timeout=15,
    )
    if resp.status_code != 200:
        print(f"❌ Token exchange failed (HTTP {resp.status_code}): {resp.text}")
        return None
    return resp.json()


def fetch_userinfo(access_token):
    """Fetch person ID and name from the userinfo endpoint."""
    try:
        resp = requests.get(
            USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15,
        )
        if resp.status_code == 200:
            return resp.json()
        print(f"⚠️  Could not fetch userinfo (HTTP {resp.status_code}): {resp.text}")
    except Exception as e:
        print(f"⚠️  Could not fetch userinfo: {e}")
    return None


def main():
    print("=" * 55)
    print("  LinkedIn OAuth 2.0 Authorization Helper")
    print("=" * 55)

    # Get client ID
    client_id = CLIENT_ID
    if not client_id:
        client_id = input("\nEnter your LinkedIn Client ID: ").strip()
    if not client_id:
        print("❌ Client ID is required.")
        sys.exit(1)

    # Get client secret
    client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
    if not client_secret:
        client_secret = input("\nEnter your LinkedIn Client Secret: ").strip()
    if not client_secret:
        print("❌ Client secret is required.")
        sys.exit(1)

    print(f"\n📋 Client ID:     {CLIENT_ID}")
    print(f"📋 Redirect URI:  {REDIRECT_URI}")
    print(f"📋 Scopes:        {SCOPES}")

    print("\n" + "=" * 55)
    print("  Make sure you've added this redirect URI to your LinkedIn app:")
    print(f"  → {REDIRECT_URI}")
    print("  (LinkedIn Developers → your app → Auth tab → Redirect URLs)")
    print("=" * 55)

    input("\nPress Enter when ready to open your browser...")

    # Open browser
    url = build_auth_url(client_id)
    print(f"\n🌐 Opening browser to LinkedIn authorization page...")
    print(f"   (If it doesn't open, copy this URL manually:\n   {url})\n")
    webbrowser.open(url)

    # Start local server to catch callback
    server = HTTPServer(("localhost", PORT), CallbackHandler)
    server.auth_code = None
    print(f"⏳ Waiting for LinkedIn to redirect back to localhost:{PORT}...")
    print("   (This window will close automatically once you authorize)")

    server.handle_request()  # handle one request (the callback)

    if not server.auth_code:
        print("❌ No authorization code received. Please try again.")
        sys.exit(1)

    # Exchange code for tokens
    print("🔄 Exchanging authorization code for tokens...")
    tokens = exchange_code(server.auth_code, client_secret, client_id)
    if not tokens:
        sys.exit(1)

    access_token = tokens.get("access_token", "")
    refresh_token = tokens.get("refresh_token", "")
    expires_in = tokens.get("expires_in", "")

    print("\n" + "=" * 55)
    print("  ✅ SUCCESS! Here are your tokens:")
    print("=" * 55)
    print(f"\n  LINKEDIN_ACCESS_TOKEN={access_token}")
    print(f"  LINKEDIN_REFRESH_TOKEN={refresh_token}")
    print(f"  (access token expires in {expires_in} seconds)")

    # Try to fetch person ID
    userinfo = fetch_userinfo(access_token)
    if userinfo:
        sub = userinfo.get("sub", "")
        name = userinfo.get("name", "")
        print(f"\n  LINKEDIN_MEMBER_URN=urn:li:person:{sub}")
        if name:
            print(f"  (Authenticated as: {name})")

    print("\n" + "=" * 55)
    print("  📝 Copy the lines above into your .env file:")
    print("=" * 55)
    print(f"  LINKEDIN_ACCESS_TOKEN={access_token}")
    if refresh_token:
        print(f"  LINKEDIN_REFRESH_TOKEN={refresh_token}")
    if userinfo and userinfo.get("sub"):
        print(f"  LINKEDIN_MEMBER_URN=urn:li:person:{userinfo['sub']}")
    print("=" * 55)

    # Also offer to save directly to .env
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        answer = input("\nSave these to your .env file automatically? (y/n): ").strip().lower()
        if answer == "y":
            update_env_file(env_path, {
                "LINKEDIN_ACCESS_TOKEN": access_token,
                "LINKEDIN_REFRESH_TOKEN": refresh_token,
            })
            if userinfo and userinfo.get("sub"):
                update_env_file(env_path, {
                    "LINKEDIN_MEMBER_URN": f"urn:li:person:{userinfo['sub']}",
                })
            print(f"✅ Saved to {env_path}")
        else:
            print("👌 No problem — copy them manually into your .env file.")

    print("\n🎉 You're all set! You can now run: python main.py")


def update_env_file(path, updates):
    """Update or add key=value lines in an .env file."""
    lines = []
    if os.path.exists(path):
        with open(path, "r") as f:
            lines = f.readlines()
    # Remove existing keys
    keys = set(updates.keys())
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if "=" in stripped:
            key = stripped.split("=")[0]
            if key in keys:
                continue  # will be re-added
        new_lines.append(line)
    # Append new values
    for k, v in updates.items():
        if v:
            new_lines.append(f"{k}={v}\n")
    with open(path, "w") as f:
        f.writelines(new_lines)


if __name__ == "__main__":
    main()

"""
get_linkedin_token.py  (OPTIONAL helper - apne computer par chalao)
---------------------------------------------------------------------
LinkedIn access token + person URN ek command mein nikaalta hai.
(Developer portal ka "OAuth 2.0 tools" bhi kaam karta hai - ye uska
alternative hai.)

Ek baar ki setup:
  developer.linkedin.com > apni app > Auth tab > "Authorized redirect URLs"
  mein ye add karo:   http://localhost:8765/callback

Chalao:
  pip install requests
  python scripts/get_linkedin_token.py

Ye Client ID / Client Secret poochega (Auth tab mein milte hain), browser
kholega, tum "Allow" dabaoge, aur terminal mein token + URN print ho jayega.
Wo dono GitHub Secrets mein daal do. Kuch bhi file mein save nahi hota.
"""

import getpass
import secrets
import webbrowser
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import requests

PORT = 8765
REDIRECT_URI = f"http://localhost:{PORT}/callback"
SCOPES = "openid profile w_member_social"


def main():
    client_id = input("LinkedIn Client ID: ").strip()
    client_secret = getpass.getpass("LinkedIn Client Secret (type karte waqt dikhega nahi): ").strip()
    state = secrets.token_urlsafe(16)
    result = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            params = parse_qs(urlparse(self.path).query)
            result.update({k: v[0] for k, v in params.items()})
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write("<h2>Ho gaya! Ab terminal par wapas jao.</h2>".encode())

        def log_message(self, *args):
            pass

    auth_url = "https://www.linkedin.com/oauth/v2/authorization?" + urlencode({
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "state": state,
        "scope": SCOPES,
    })
    print("\nBrowser khul raha hai. Na khule to ye link khud kholo:\n" + auth_url + "\n")
    webbrowser.open(auth_url)

    server = HTTPServer(("localhost", PORT), Handler)
    while "code" not in result and "error" not in result:
        server.handle_request()

    if "error" in result:
        raise SystemExit(f"LinkedIn ne mana kiya: {result.get('error_description', result['error'])}")
    if result.get("state") != state:
        raise SystemExit("State match nahi hua - dobara try karo.")

    token_resp = requests.post(
        "https://www.linkedin.com/oauth/v2/accessToken",
        data={
            "grant_type": "authorization_code",
            "code": result["code"],
            "redirect_uri": REDIRECT_URI,
            "client_id": client_id,
            "client_secret": client_secret,
        },
        timeout=30,
    )
    token_resp.raise_for_status()
    data = token_resp.json()
    token = data["access_token"]
    expires = datetime.now() + timedelta(seconds=int(data.get("expires_in", 0)))

    info = requests.get(
        "https://api.linkedin.com/v2/userinfo",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    ).json()

    print("\n================ RESULT ================")
    print("LINKEDIN_ACCESS_TOKEN =", token)
    print("LINKEDIN_PERSON_URN   =", f"urn:li:person:{info.get('sub', '???')}")
    print("Naam                  =", info.get("name", "?"))
    print("Expire hoga           =", expires.strftime("%d %b %Y"))
    print("=========================================")
    print("Ye dono values GitHub > Settings > Secrets and variables > Actions mein daalo.")


if __name__ == "__main__":
    main()

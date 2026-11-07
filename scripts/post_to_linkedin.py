"""
post_to_linkedin.py
----------------------
LinkedIn "Posts API" (/rest/posts) se text post publish karta hai.

Kya-kya handle karta hai:
- Post se PEHLE token check (taaki token kharab ho to OpenAI ka paisa
  bekaar na jaye) aur saaf Roman-Urdu error message.
- LINKEDIN_PERSON_URN na diya ho to token se khud nikaal leta hai.
- LinkedIn ke "little text" format ke liye special characters escape
  karta hai. (Bina escape ke ( ) [ ] @ jaise characters par post kat
  jata hai ya fail ho jata hai.) Hashtags clickable bante hain.
- LinkedIn-Version header khud current month ke hisaab se set hota hai,
  isliye saal baad "version expired" error nahi aayega.
"""

import os
import re
from datetime import datetime, timezone

import requests

POSTS_URL = "https://api.linkedin.com/rest/posts"
USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
TIMEOUT = 30

FRIENDLY_ERRORS = {
    "EXPIRED_ACCESS_TOKEN": (
        "LinkedIn token EXPIRE ho gaya hai (har 60 din mein hota hai). "
        "Naya token banao: README.md > 'Token renew karna' dekho, phir GitHub "
        "Secret LINKEDIN_ACCESS_TOKEN update karo."
    ),
    "DISABLED_APPLICATION": (
        "Tumhari LinkedIn Developer App DISABLED hai. developer.linkedin.com/apps "
        "par jaake app check karo. Agar wahan restore ka option na ho to nayi app "
        "banao (README.md > Part C), aur naya token GitHub Secret mein daalo."
    ),
    "REVOKED_ACCESS_TOKEN": (
        "LinkedIn token revoke ho chuka hai (password change ya app access hataya "
        "gaya). Naya token banao aur GitHub Secret update karo."
    ),
    "INVALID_ACCESS_TOKEN": (
        "LinkedIn token galat hai. GitHub Secret LINKEDIN_ACCESS_TOKEN mein poora "
        "token bina extra space ke paste karo."
    ),
}


class LinkedInAuthError(RuntimeError):
    pass


def api_version():
    """LinkedIn-Version header (YYYYMM). 2 mahine purana version - hamesha supported."""
    if os.environ.get("LINKEDIN_API_VERSION"):
        return os.environ["LINKEDIN_API_VERSION"]
    now = datetime.now(timezone.utc)
    year, month = now.year, now.month - 2
    if month <= 0:
        year, month = year - 1, month + 12
    return f"{year}{month:02d}"


def _token():
    token = (os.environ.get("LINKEDIN_ACCESS_TOKEN") or "").strip()
    if not token:
        raise LinkedInAuthError(
            "LINKEDIN_ACCESS_TOKEN set nahi hai. GitHub Secrets mein add karo (README.md)."
        )
    return token


def _explain(response):
    """LinkedIn ke error ko samajhne layak message mein badlo."""
    try:
        data = response.json()
    except ValueError:
        data = {}
    code = data.get("code", "")
    friendly = FRIENDLY_ERRORS.get(code)
    raw = f"Status {response.status_code}, code={code or '-'}, message={data.get('message') or response.text[:300]}"
    return f"{friendly} ({raw})" if friendly else f"LinkedIn error: {raw}"


def check_linkedin_auth():
    """
    Token valid hai ya nahi, ye check karta hai aur person URN return karta hai.
    Token expired / app disabled ho to LinkedInAuthError raise karta hai.
    """
    token = _token()
    env_urn = (os.environ.get("LINKEDIN_PERSON_URN") or "").strip()

    response = requests.get(
        USERINFO_URL, headers={"Authorization": f"Bearer {token}"}, timeout=TIMEOUT
    )

    if response.status_code == 200:
        sub = response.json().get("sub", "")
        token_urn = f"urn:li:person:{sub}" if sub else ""
        if env_urn and token_urn and env_urn != token_urn:
            print(
                f"  Warning: LINKEDIN_PERSON_URN ({env_urn}) token wale account "
                f"({token_urn}) se match nahi karta. Token wala use ho raha hai."
            )
        return token_urn or env_urn

    if response.status_code == 401:
        raise LinkedInAuthError(_explain(response))

    # 403 = token mein 'openid profile' scope nahi hai. Token shayad theek ho,
    # isliye URN secret se le lo aur aage badho.
    if not env_urn:
        raise LinkedInAuthError(
            "Token se profile ID nahi mil saki (scope 'openid profile' missing). "
            "Ya to naya token 'openid profile w_member_social' scopes ke saath "
            "banao, ya LINKEDIN_PERSON_URN secret add karo. " + _explain(response)
        )
    return env_urn


# ---------------------------------------------------------------------------
# LinkedIn "little text" format
# ---------------------------------------------------------------------------
_RESERVED = set("\\|{}@[]()<>#*_~")


def _escape(text):
    return "".join(f"\\{ch}" if ch in _RESERVED else ch for ch in text)


def to_little_text(text):
    """Plain text ko LinkedIn commentary format mein badlo. #tags clickable bante hain."""
    out = []
    last = 0
    for m in re.finditer(r"(?<![\w&])#([A-Za-z][A-Za-z0-9_]*)", text):
        out.append(_escape(text[last:m.start()]))
        out.append("{hashtag|\\#|" + m.group(1) + "}")
        last = m.end()
    out.append(_escape(text[last:]))
    return "".join(out)


def post_to_linkedin(post_text, person_urn=None):
    """Post publish karta hai. Return: LinkedIn post ID (urn:li:share:...)."""
    token = _token()
    person_urn = person_urn or check_linkedin_auth()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": api_version(),
    }
    payload = {
        "author": person_urn,
        "commentary": to_little_text(post_text),
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": [],
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False,
    }

    response = requests.post(POSTS_URL, headers=headers, json=payload, timeout=TIMEOUT)
    if response.status_code not in (200, 201):
        if response.status_code == 401:
            raise LinkedInAuthError(_explain(response))
        raise RuntimeError("LinkedIn post fail hua. " + _explain(response))

    return response.headers.get("x-restli-id", "")


if __name__ == "__main__":
    # Sirf token check (kuch post nahi karta):  python scripts/post_to_linkedin.py
    urn = check_linkedin_auth()
    print(f"Token theek hai. Profile: {urn}  (API version {api_version()})")

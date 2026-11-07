"""
run_all.py
-----------
Poora automation is order mein chalata hai:
    0. LinkedIn token check (sabse pehle, taaki problem turant pata chale)
    1. Market research: news fetch (RSS, free)
    2. AI se research brief + insaan jaisa post (OpenAI)
    3. LinkedIn par publish
    4. Result docs/history.json mein save (dashboard ke liye)

GitHub Actions isi file ko roz chalata hai.

Environment options:
    DRY_RUN=true      -> post banega, dashboard par dikhega, LinkedIn par NAHI jayega
    FORCE=true        -> aaj already post ho chuka ho tab bhi dobara post karo
    POST_FORMAT=story -> format fix karo (story/contrarian/breakdown/practical/question)
    LINKEDIN_TOKEN_CREATED=2026-11-07 -> token banane ki date; 50 din baad warning
"""

import json
import os
import sys
from datetime import date, datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetch_news import fetch_ai_news  # noqa: E402
from generate_post import generate_linkedin_post  # noqa: E402
from post_to_linkedin import LinkedInAuthError, check_linkedin_auth, post_to_linkedin  # noqa: E402

HISTORY_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "docs", "history.json"
)
MAX_HISTORY = 90


def _flag(name):
    return os.environ.get(name, "").strip().lower() in ("1", "true", "yes")


def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def save_history(history):
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history[:MAX_HISTORY], f, ensure_ascii=False, indent=2)


def gh_annotation(level, message):
    """GitHub Actions run page par warning/error box dikhata hai."""
    if os.environ.get("GITHUB_ACTIONS"):
        print(f"::{level}::{message}")


def token_age_warning():
    created = os.environ.get("LINKEDIN_TOKEN_CREATED", "").strip()
    if not created:
        return
    try:
        age = (date.today() - date.fromisoformat(created)).days
    except ValueError:
        return
    if age >= 50:
        msg = f"LinkedIn token {age} din purana hai - 60 din par expire hoga. Jaldi renew karo."
        print("  " + msg)
        gh_annotation("warning", msg)


def run():
    now = datetime.now(timezone.utc)
    history = load_history()
    dry_run = _flag("DRY_RUN")

    already_today = any(
        r.get("status") == "success" and r.get("date", "").startswith(now.strftime("%Y-%m-%d"))
        for r in history
    )
    if already_today and not dry_run and not _flag("FORCE"):
        print("Aaj ka post already publish ho chuka hai. (Dobara ke liye FORCE=true)")
        return

    record = {
        "date": now.strftime("%Y-%m-%d %H:%M UTC"),
        "status": "failed",
        "headline": "",
        "topic": "",
        "format": "",
        "source_link": "",
        "post_text": "",
        "post_preview": "",
        "linkedin_post_id": "",
        "error": "",
    }

    auth_error = None
    person_urn = None
    try:
        # Step 0: LinkedIn check
        if not dry_run:
            print("Step 0: LinkedIn token check...")
            token_age_warning()
            try:
                person_urn = check_linkedin_auth()
                print(f"  Token theek hai ({person_urn}).")
            except LinkedInAuthError as e:
                # Post phir bhi banayenge taaki dashboard se copy karke manually daal sako
                auth_error = str(e)
                print(f"  PROBLEM: {auth_error}")
                gh_annotation("error", auth_error)

        # Step 1: Research
        print("Step 1: Market research (news fetch)...")
        published = [r for r in history if r.get("status") == "success"]
        recent_titles = [r.get("news_title") or r.get("headline", "") for r in published[:30]]
        news_items = fetch_ai_news(already_posted_titles=recent_titles)
        if not news_items:
            raise ValueError("Koi nayi news nahi mili RSS feeds se.")
        print(f"  {len(news_items)} news items mile.")

        # Step 2: Write
        print("Step 2: AI se post likhwa rahe hain...")
        recent_openings = [
            r["post_text"].split("\n", 1)[0] for r in published[:10] if r.get("post_text")
        ]
        result = generate_linkedin_post(
            news_items,
            recent_posts=[r.get("headline", "") for r in published[:10] if r.get("headline")],
            recent_openings=recent_openings,
        )
        post_text = result["text"]
        record.update({
            "headline": result["headline"],
            "news_title": result["news_title"],
            "topic": result["topic"],
            "format": result["format"],
            "source_link": result["link"],
            "post_text": post_text,
            "post_preview": post_text[:200],
        })
        print(f"  Post tayyar ({len(post_text.split())} words).\n")
        print("-" * 60 + "\n" + post_text + "\n" + "-" * 60)

        # Step 3: Publish
        if dry_run:
            record["status"] = "dry_run"
            print("DRY_RUN: LinkedIn par post nahi kiya.")
        elif auth_error:
            raise LinkedInAuthError(auth_error)
        else:
            print("Step 3: LinkedIn par publish...")
            record["linkedin_post_id"] = post_to_linkedin(post_text, person_urn=person_urn)
            record["status"] = "success"
            print(f"  Post publish ho gaya! {record['linkedin_post_id']}")

    except Exception as e:
        print(f"ERROR: {e}")
        record["error"] = str(e)
        if not auth_error:
            gh_annotation("error", str(e))

    history.insert(0, record)
    save_history(history)
    print("History file update ho gayi.")

    if record["status"] == "failed":
        sys.exit(1)   # GitHub Actions run laal hoga + email alert


if __name__ == "__main__":
    run()

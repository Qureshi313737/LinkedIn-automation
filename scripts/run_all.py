"""
run_all.py
-----------
Poora automation is order mein chalata hai:
    1. News fetch karo (RSS se, free)
    2. AI se professional post likhwao (OpenAI)
    3. LinkedIn par publish karo
    4. Result ko docs/history.json mein save karo (dashboard ke liye)

GitHub Actions isi file ko roz automatically chalata hai.
Isme kuch edit karne ki zaroorat NAHI hai.
"""

import os
import sys
import json
from datetime import datetime, timezone

# scripts/ folder ke andar ke doosre files import karne ke liye
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fetch_news import fetch_ai_news
from generate_post import generate_linkedin_post
from post_to_linkedin import post_to_linkedin

# repo root se docs/history.json tak ka path
HISTORY_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "docs", "history.json"
)


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
        json.dump(history, f, ensure_ascii=False, indent=2)


def run():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    history = load_history()

    record = {
        "date": today,
        "status": "failed",
        "post_preview": "",
        "error": "",
    }

    try:
        print("Step 1: News fetch ho raha hai...")
        news_items = fetch_ai_news()
        if not news_items:
            raise ValueError("Koi news nahi mili RSS feeds se.")
        print(f"  {len(news_items)} news items mile.")

        print("Step 2: AI se post generate ho raha hai...")
        post_text = generate_linkedin_post(news_items)
        print(f"  Post generate hua ({len(post_text)} characters).")

        print("Step 3: LinkedIn par publish ho raha hai...")
        post_to_linkedin(post_text)
        print("  Post successfully publish ho gaya!")

        record["status"] = "success"
        record["post_preview"] = post_text[:200]

    except Exception as e:
        print(f"ERROR: {e}")
        record["error"] = str(e)

    history.insert(0, record)   # naya record sabse upar dikhega
    history = history[:60]       # sirf last 60 records rakho, file chhoti rahegi
    save_history(history)
    print("History file update ho gayi.")

    if record["status"] == "failed":
        sys.exit(1)   # GitHub Actions ko batao ki run fail hua (email alert milega)


if __name__ == "__main__":
    run()

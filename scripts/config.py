"""
config.py
----------
Repo root ki config.json padhta hai. Agar koi setting missing ho to
default value use hoti hai, taaki system kabhi config ki wajah se na ruke.
"""

import json
import os

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_FILE = os.path.join(ROOT_DIR, "config.json")

DEFAULTS = {
    "author_persona": "I work in tech and follow the AI industry closely.",
    "post_language": "English",
    "min_words": 120,
    "max_words": 220,
    "max_hashtags": 3,
    "include_source_link": False,
    "openai_model": "gpt-4o",
    "topics": [{"name": "AI industry", "query": "artificial intelligence"}],
    "extra_rss_feeds": [],
    "news_max_age_hours": 36,
    "max_news_items": 25,
}


def load_config():
    config = dict(DEFAULTS)
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            user_config = json.load(f)
        config.update({k: v for k, v in user_config.items() if not k.startswith("_")})
    # Environment variable se model override (GitHub Variables ke through)
    if os.environ.get("OPENAI_MODEL"):
        config["openai_model"] = os.environ["OPENAI_MODEL"]
    return config

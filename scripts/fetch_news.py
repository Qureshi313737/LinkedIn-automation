"""
fetch_news.py
--------------
Market research ka pehla step: Google News (har topic ke liye) aur kuch
tech-news RSS feeds se taaza khabrein nikalta hai.

- Koi API key nahi chahiye (public RSS feeds), 100% free.
- Sirf pichle `news_max_age_hours` ghanton ki news rakhta hai.
- Duplicate headlines hata deta hai.
- Jo story pehle post ho chuki hai, use dobara nahi uthata.

Topics / feeds badalne ke liye config.json edit karo, ye file nahi.
"""

import html
import re
import sys
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import load_config  # noqa: E402

ATOM = "{http://www.w3.org/2005/Atom}"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; NewsDigestBot/1.0)"}
REQUEST_TIMEOUT = 20


def google_news_url(query):
    q = quote_plus(f"{query} when:1d")
    return f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"


def _clean_text(raw):
    """HTML tags hatao, entities decode karo, extra spaces hatao."""
    if not raw:
        return ""
    text = re.sub(r"<[^>]+>", " ", raw)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_date(value):
    if not value:
        return None
    value = value.strip()
    try:
        dt = parsedate_to_datetime(value)          # RSS: "Tue, 05 Nov 2026 10:00:00 GMT"
    except (TypeError, ValueError):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))  # Atom: ISO 8601
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_feed(xml_bytes, topic=""):
    """RSS 2.0 ya Atom feed ko list of dicts mein badalta hai."""
    root = ET.fromstring(xml_bytes)
    items = []

    # RSS 2.0
    for node in root.iter("item"):
        title = _clean_text(node.findtext("title"))
        source = _clean_text(node.findtext("source"))
        # Google News title ke end mein " - Publisher" hota hai, use alag karo
        if source and title.endswith(f" - {source}"):
            title = title[: -len(f" - {source}")].strip()
        summary = _clean_text(node.findtext("description"))
        if summary.startswith(title):          # Google News summary = title + source
            summary = ""
        items.append({
            "title": title,
            "summary": summary[:600],
            "link": (node.findtext("link") or "").strip(),
            "source": source,
            "published": _parse_date(node.findtext("pubDate")),
            "topic": topic,
        })

    # Atom
    for node in root.iter(f"{ATOM}entry"):
        # Note: Element ki truthiness children par depend karti hai, isliye "is None"
        link_el = node.find(f"{ATOM}link[@rel='alternate']")
        if link_el is None:
            link_el = node.find(f"{ATOM}link")
        summary = node.findtext(f"{ATOM}summary") or node.findtext(f"{ATOM}content")
        items.append({
            "title": _clean_text(node.findtext(f"{ATOM}title")),
            "summary": _clean_text(summary)[:600],
            "link": link_el.get("href", "").strip() if link_el is not None else "",
            "source": "",
            "published": _parse_date(
                node.findtext(f"{ATOM}published") or node.findtext(f"{ATOM}updated")
            ),
            "topic": topic,
        })

    return [i for i in items if i["title"]]


def _title_key(title):
    words = re.findall(r"[a-z0-9]+", title.lower())
    return " ".join(words[:10])


def _download(url):
    response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.content


def fetch_ai_news(already_posted_titles=None, config=None):
    """
    Saare sources padhta hai aur list return karta hai, sabse nayi news pehle:
    [{"title", "summary", "link", "source", "published", "topic"}, ...]
    """
    config = config or load_config()
    already_posted = {_title_key(t) for t in (already_posted_titles or []) if t}

    sources = [(google_news_url(t["query"]), t["name"]) for t in config["topics"]]
    sources += [(url, "Tech news") for url in config["extra_rss_feeds"]]

    cutoff = datetime.now(timezone.utc) - timedelta(hours=config["news_max_age_hours"])
    seen = set()
    collected = []

    for url, topic in sources:
        try:
            entries = parse_feed(_download(url), topic=topic)
        except Exception as e:
            # Ek feed fail ho jaye to poora system na ruke
            print(f"[fetch_news] Warning: feed skip kiya ({url[:70]}...): {e}")
            continue

        for item in entries[:15]:
            if item["published"] and item["published"] < cutoff:
                continue
            key = _title_key(item["title"])
            if key in seen or key in already_posted:
                continue
            seen.add(key)
            collected.append(item)

    oldest = datetime(1970, 1, 1, tzinfo=timezone.utc)
    collected.sort(key=lambda i: i["published"] or oldest, reverse=True)
    return collected[: config["max_news_items"]]


if __name__ == "__main__":
    # Standalone test: python scripts/fetch_news.py
    news = fetch_ai_news()
    print(f"Total {len(news)} news items mile:\n")
    for i, item in enumerate(news, 1):
        when = item["published"].strftime("%Y-%m-%d %H:%M") if item["published"] else "?"
        print(f"{i}. [{item['topic']}] {item['title']} ({item['source'] or 'feed'}, {when})")

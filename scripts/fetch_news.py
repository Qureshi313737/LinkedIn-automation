"""
fetch_news.py
--------------
Google News aur tech-news RSS feeds se aaj ki AI-related news nikalta hai.
Koi API key nahi chahiye - ye sab public RSS feeds hain, isliye 100% free.

Kuch bhi edit nahi karna is file mein - sab kuch ready hai.
Agar tum apni marzi ke topics chahte ho (sirf "AI" ke alawa), to neeche
RSS_FEEDS list mein URL badal sakte ho - warna default rehne do.
"""

import feedparser

# In feeds ko yahan se add/remove/edit kar sakte ho (optional)
RSS_FEEDS = [
    "https://news.google.com/rss/search?q=artificial+intelligence+when:1d&hl=en-US&gl=US&ceid=US:en",
    "https://techcrunch.com/category/artificial-intelligence/feed/",
    "https://venturebeat.com/category/ai/feed/",
]

MAX_ITEMS_PER_FEED = 5
MAX_TOTAL_ITEMS = 10


def fetch_ai_news():
    """
    Saare RSS feeds padhta hai aur ek list return karta hai:
    [{"title": ..., "summary": ..., "link": ..., "published": ...}, ...]
    """
    all_items = []

    for feed_url in RSS_FEEDS:
        try:
            parsed = feedparser.parse(feed_url)
            for entry in parsed.entries[:MAX_ITEMS_PER_FEED]:
                item = {
                    "title": getattr(entry, "title", "").strip(),
                    "summary": getattr(entry, "summary", "").strip(),
                    "link": getattr(entry, "link", "").strip(),
                    "published": getattr(entry, "published", ""),
                }
                if item["title"]:
                    all_items.append(item)
        except Exception as e:
            # Ek feed fail ho jaye to poora system na roke - agle feed pe badho
            print(f"[fetch_news] Warning: could not read feed {feed_url}: {e}")
            continue

    return all_items[:MAX_TOTAL_ITEMS]


if __name__ == "__main__":
    # Standalone test ke liye: python scripts/fetch_news.py
    news = fetch_ai_news()
    print(f"Total {len(news)} news items mile:\n")
    for i, item in enumerate(news, 1):
        print(f"{i}. {item['title']}")
        print(f"   {item['link']}\n")

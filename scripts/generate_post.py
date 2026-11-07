"""
generate_post.py
------------------
News se LinkedIn post banata hai, 3 steps mein:

  1. RESEARCH  - AI saari news padhkar sabse important story chunta hai aur
                 sirf usi ke facts ka ek "brief" banata hai (kuch invent nahi).
  2. WRITE     - Us brief se ek insaan jaisa post likhta hai. Har din alag
                 format (story / contrarian / breakdown / ...) taaki posts
                 ek jaise na lagein.
  3. HUMANIZE  - Typical "AI wale" words/patterns (delve, game-changer,
                 em-dash, etc.) check karta hai. Mile to dobara likhwata hai,
                 phir chhoti-moti safai khud karta hai.

OPENAI_API_KEY environment variable chahiye (GitHub Secrets se aata hai).
Is file mein apni key kabhi type mat karna.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone

from openai import OpenAI, BadRequestError

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from config import load_config  # noqa: E402

# ---------------------------------------------------------------------------
# Har din ka post format (rotation) - posts repetitive na lagein
# ---------------------------------------------------------------------------
POST_FORMATS = {
    "story": (
        "Open with the single most concrete detail from the news (a number, a "
        "name, a decision). Then explain what actually happened in plain words, "
        "then give your honest take on what it means."
    ),
    "contrarian": (
        "Open with what most people will probably get wrong or overhype about "
        "this news. Then explain the more grounded reading, using the facts."
    ),
    "breakdown": (
        "Open with a one-line hook. Then give 3 short numbered takeaways "
        "(plain '1.' '2.' '3.' lines, no emojis as bullets). Close with your "
        "own one-line view."
    ),
    "practical": (
        "Focus on what this changes in practice for people who build products, "
        "run businesses or plan careers. Be concrete about who is affected and how."
    ),
    "question": (
        "Open with a genuine, specific question the news raises. Walk through "
        "the facts, then say where you lean and why."
    ),
}

# ---------------------------------------------------------------------------
# Human writing style guide
# ---------------------------------------------------------------------------
STYLE_GUIDE = """How to sound like a real person, not an AI:
- Write the way a sharp professional types a LinkedIn post themselves: direct,
  a bit informal, clearly opinionated. Not a press release, not a blog intro.
- Mix very short sentences with longer ones. Use a few one-line paragraphs.
- Use contractions (it's, don't, they're) and plain everyday words.
- Use the specific names and numbers from the facts. Specific beats vague.
- First person opinions are good ("I think", "My read:", "Honestly,").
  But NEVER invent personal experiences, clients, meetings or anecdotes.
- No em dashes or en dashes. Use commas, periods or a simple hyphen instead.
- No markdown: no **bold**, no headings, no bullet symbols like • or emoji bullets.
- At most one emoji, and only if it really fits. Zero is fine.
- Don't stack three adjectives or use "X, Y, and Z" triplets for rhythm.
- Never use these words/phrases: delve, game-changer, landscape, fast-paced,
  ever-evolving, revolutionize, unlock, unleash, harness, leverage, navigate,
  realm, tapestry, testament, paradigm, seamless, cutting-edge, groundbreaking,
  transformative, synergy, embark, elevate, "in today's world",
  "it's not just X, it's Y", "buckle up", "let that sink in", "a new era",
  "excited to share", "stay tuned", "the future is here".
- End with ONE specific question people can actually answer (not just
  "Thoughts?" or "What do you think?").
"""

BANNED_PATTERNS = [
    r"\bdelv(e|es|ing)\b", r"game[- ]changer", r"\blandscape\b", r"fast[- ]paced",
    r"ever[- ]evolving", r"\brevolutioni[sz]", r"\bunlock", r"\bunleash", r"\bharness",
    r"\bleverag", r"\bnavigat", r"\brealm\b", r"\btapestry\b", r"\btestament\b",
    r"\bparadigm", r"\bseamless", r"cutting[- ]edge", r"\bgroundbreaking\b",
    r"\btransformative\b", r"\bsynerg", r"\bembark", r"\belevate", r"in today'?s",
    r"buckle up", r"let that sink in", r"a new era", r"excited to share",
    r"stay tuned", r"the future is here", r"it'?s not just", r"—", r"–",
    r"\*\*",
]

SYSTEM_RESEARCH = """You are a careful market and technology news analyst.
You only use facts that appear in the provided news items. You never invent
names, numbers, dates or quotes. Reply with valid JSON only."""


def _client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY set nahi hai. GitHub repo > Settings > Secrets and "
            "variables > Actions mein add karo (README.md dekho)."
        )
    return OpenAI(api_key=api_key)


def _chat(client, model, messages, temperature=0.7, json_mode=False):
    """OpenAI call. Kuch naye models temperature support nahi karte - fallback."""
    kwargs = {"model": model, "messages": messages}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    try:
        response = client.chat.completions.create(temperature=temperature, **kwargs)
    except BadRequestError as e:
        if "temperature" not in str(e):
            raise
        response = client.chat.completions.create(**kwargs)
    return (response.choices[0].message.content or "").strip()


def _format_news(news_items):
    lines = []
    for i, item in enumerate(news_items):
        when = item["published"].strftime("%Y-%m-%d %H:%M UTC") if item.get("published") else "unknown"
        lines.append(f"[{i}] ({item.get('topic', '')}) {item['title']}")
        if item.get("source"):
            lines.append(f"    Publisher: {item['source']}")
        lines.append(f"    Published: {when}")
        if item.get("summary"):
            lines.append(f"    Summary: {item['summary']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Step 1: Research
# ---------------------------------------------------------------------------
def build_research_brief(client, model, news_items, recent_posts):
    recent = "\n".join(f"- {p}" for p in recent_posts[:10]) or "- (none)"
    prompt = f"""Today's news items:

{_format_news(news_items)}

Topics I already posted about recently (avoid repeating these):
{recent}

Task: pick the ONE story that is the most significant and genuinely new for a
professional audience interested in AI, tech and markets (a real launch, deal,
funding round, earnings result, regulation, research result or market move).
Prefer stories with concrete facts. Skip opinion pieces, listicles and rumours.

Return JSON with exactly these keys:
{{
  "chosen_index": <number from the list>,
  "headline": "<short neutral headline>",
  "publisher": "<publisher name if known, else empty string>",
  "key_facts": ["<fact taken directly from the items>", "..."],
  "related_context": ["<supporting facts from OTHER items in the list, if relevant>"],
  "why_it_matters": "<1-2 sentences, reasoning only from the facts>",
  "angle": "<a specific, interesting point of view a thoughtful professional could take>"
}}"""
    raw = _chat(
        client, model,
        [{"role": "system", "content": SYSTEM_RESEARCH}, {"role": "user", "content": prompt}],
        temperature=0.3, json_mode=True,
    )
    brief = json.loads(raw)
    idx = int(brief.get("chosen_index", 0))
    if not 0 <= idx < len(news_items):
        idx = 0
    brief["chosen_index"] = idx
    return brief


# ---------------------------------------------------------------------------
# Step 2 + 3: Write and humanize
# ---------------------------------------------------------------------------
def find_ai_tells(text):
    """Text mein jo 'AI jaise' patterns mile, unki list."""
    found = []
    for pattern in BANNED_PATTERNS:
        m = re.search(pattern, text, flags=re.IGNORECASE)
        if m:
            found.append(m.group(0))
    return found


def clean_post(text, max_hashtags):
    """Deterministic safai: dashes, markdown, extra hashtags, extra blank lines."""
    text = text.strip().strip('"').strip()
    text = re.sub(r"^(here('s| is) (your|the) post:?\s*)", "", text, flags=re.IGNORECASE)
    text = text.replace("**", "").replace("__", "")
    text = re.sub(r"\s*[—–]\s*", " - ", text)          # em/en dash
    text = text.replace("“", '"').replace("”", '"').replace("’", "'")

    # Hashtags limit karo (sirf pehle N rakho)
    count = 0

    def _limit(match):
        nonlocal count
        count += 1
        return match.group(0) if count <= max_hashtags else ""

    text = re.sub(r"[ \t]*#\w+", _limit, text)

    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _pick_format(override=None):
    if override and override in POST_FORMATS:
        return override
    names = list(POST_FORMATS)
    day = datetime.now(timezone.utc).timetuple().tm_yday
    return names[day % len(names)]


def write_post(client, model, brief, config, post_format, recent_openings):
    openings = "\n".join(f"- {o}" for o in recent_openings[:7]) or "- (none)"
    source_line = ""
    if config.get("include_source_link") and brief.get("link"):
        source_line = f"Put this source link on its own line just before the hashtags: {brief['link']}\n"

    prompt = f"""About me (the author): {config['author_persona']}

Research brief (the ONLY facts you may use):
{json.dumps({k: brief.get(k) for k in ("headline", "publisher", "key_facts", "related_context", "why_it_matters", "angle")}, indent=2, ensure_ascii=False)}

Write my LinkedIn post about this.

Structure for today: {POST_FORMATS[post_format]}

Rules:
- Language: {config['post_language']}.
- Length: {config['min_words']} to {config['max_words']} words.
- If a publisher is known, mention it naturally once (e.g. "according to Reuters").
- Do not open the same way as my recent posts. Recent openings:
{openings}
- End with one specific question, then {config['max_hashtags']} or fewer relevant hashtags on the last line.
{source_line}
{STYLE_GUIDE}

Output only the post text, nothing else."""

    messages = [
        {"role": "system", "content": "You ghostwrite LinkedIn posts that read as if the author typed them personally. You never invent facts."},
        {"role": "user", "content": prompt},
    ]
    text = _chat(client, model, messages, temperature=0.85)

    # Humanize pass: AI-jaise patterns mile to ek baar dobara likhwao
    tells = find_ai_tells(text)
    if tells:
        print(f"  AI-jaise patterns mile ({', '.join(sorted(set(tells)))}), rewrite ho raha hai...")
        messages += [
            {"role": "assistant", "content": text},
            {"role": "user", "content": (
                "Rewrite this so it sounds more like a real person typed it. Remove "
                f"these exact words/patterns: {', '.join(sorted(set(tells)))}. "
                "Keep every fact the same, keep the length, no em dashes. "
                "Output only the post."
            )},
        ]
        text = _chat(client, model, messages, temperature=0.7)

    return clean_post(text, config["max_hashtags"])


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------
def generate_linkedin_post(news_items, recent_posts=None, recent_openings=None, post_format=None):
    """
    news_items: fetch_news.py se mila list
    recent_posts: pichle posts ki headlines (repeat avoid karne ke liye)
    recent_openings: pichle posts ki pehli lines
    Return: dict -> {text, headline, publisher, link, topic, format}
    """
    if not news_items:
        raise ValueError("Koi news items nahi mile - post generate nahi ho sakta.")

    config = load_config()
    client = _client()
    model = config["openai_model"]

    brief = build_research_brief(client, model, news_items, recent_posts or [])
    chosen = news_items[brief["chosen_index"]]
    brief["link"] = chosen.get("link", "")
    if not brief.get("publisher"):
        brief["publisher"] = chosen.get("source", "")
    print(f"  Chuni gayi story: {chosen['title']}")

    post_format = _pick_format(post_format or os.environ.get("POST_FORMAT"))
    print(f"  Aaj ka format: {post_format}")
    text = write_post(client, model, brief, config, post_format, recent_openings or [])

    return {
        "text": text,
        "headline": brief.get("headline") or chosen["title"],
        "news_title": chosen["title"],
        "publisher": brief.get("publisher", ""),
        "link": chosen.get("link", ""),
        "topic": chosen.get("topic", ""),
        "format": post_format,
    }


if __name__ == "__main__":
    # Standalone test (LinkedIn par kuch post NAHI karta):
    #   python scripts/generate_post.py
    from fetch_news import fetch_ai_news

    result = generate_linkedin_post(fetch_ai_news())
    print("\n----- GENERATED POST -----\n")
    print(result["text"])
    print(f"\n----- ({len(result['text'].split())} words, format: {result['format']}) -----")
    print(f"Source: {result['link']}")

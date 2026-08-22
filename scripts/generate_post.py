"""
generate_post.py
------------------
News items ko OpenAI API ko bhejta hai aur ek professional LinkedIn
post likhwata hai.

ZAROORI: Isko chalane ke liye environment variable OPENAI_API_KEY set
hona chahiye. GitHub Actions mein ye tumhare "Secrets" se apne aap aata
hai (README.md mein bataya hai kaise add karna hai) - is file mein kahin
bhi apni key type NAHI karni.

Agar apne computer par local test karna ho:
    Mac/Linux:   export OPENAI_API_KEY="sk-...."
    Windows:     setx OPENAI_API_KEY "sk-...."
"""

import os
from openai import OpenAI

SYSTEM_INSTRUCTIONS = """You are a professional LinkedIn content writer covering the AI and tech industry.

Strict rule: only use facts, names, and numbers that appear in the provided
search results. Do not invent or assume any detail. If the results don't
clearly support a specific claim, leave it out.

Write the post in English only, with this format:
- 150 to 200 words
- First line must be a strong hook (a bold statement or a surprising fact)
- Body: explain what happened, why it matters, and one short personal
  insight or opinion
- Tone: professional, confident, natural - not robotic, not overly formal
- End with one short thought-provoking question, followed by 4 to 5
  relevant hashtags (e.g. #ArtificialIntelligence #AI #TechNews #Innovation
  #MachineLearning)
- Use at most 1 to 2 emojis, only if they add value

Output only the final post text. Do not include any preamble, explanation,
or phrases like "Here is your post". Start directly with the first word of
the post."""


def _format_news_for_prompt(news_items):
    """News items ko ek readable text block mein badalta hai."""
    lines = []
    for i, item in enumerate(news_items, 1):
        lines.append(f"{i}. Title: {item['title']}")
        if item.get("summary"):
            lines.append(f"   Summary: {item['summary']}")
        lines.append(f"   Source: {item['link']}")
        lines.append("")
    return "\n".join(lines)


def generate_linkedin_post(news_items):
    """
    news_items: fetch_news.py se mila hua list
    Return: final LinkedIn post text (string)
    """
    if not news_items:
        raise ValueError("Koi news items nahi mile - post generate nahi ho sakta.")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENAI_API_KEY environment variable set nahi hai. "
            "GitHub Secrets mein add karo (README.md dekho) ya local "
            "test ke liye export karo."
        )

    client = OpenAI(api_key=api_key)

    news_text = _format_news_for_prompt(news_items)
    user_message = (
        "Here are today's AI news search results:\n\n"
        f"{news_text}\n\n"
        "Based only on these results, identify the single most genuinely "
        "new AI development (new model, tool, research, or discovery). "
        "Write a professional LinkedIn post about it."
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.7,
        max_tokens=500,
        messages=[
            {"role": "system", "content": SYSTEM_INSTRUCTIONS},
            {"role": "user", "content": user_message},
        ],
    )

    post_text = response.choices[0].message.content.strip()
    return post_text


if __name__ == "__main__":
    # Standalone test ke liye: python scripts/generate_post.py
    from fetch_news import fetch_ai_news

    news = fetch_ai_news()
    post = generate_linkedin_post(news)
    print("----- GENERATED POST -----\n")
    print(post)

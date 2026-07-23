"""
google_news_fetcher.py
Fetches the top N stories from Google News' public RSS feed and formats
them into text that can be fed straight into content_generator.py, the
same way the newsletter email body is used.

Notes on the feed (undocumented but stable for years):
  - Top stories:      https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en
  - Topic feeds:      https://news.google.com/rss/headlines/section/topic/<TOPIC>
                       (TOPIC e.g. BUSINESS, TECHNOLOGY, WORLD, SPORTS, SCIENCE, HEALTH)
  - Keyword search:    https://news.google.com/rss/search?q=<QUERY>
  - Article links point to a news.google.com redirect, not the publisher's
    URL directly - that's normal for this feed.
"""

from urllib.parse import quote
import feedparser
from bs4 import BeautifulSoup

BASE_URL = "https://news.google.com/rss"


def _clean_summary(html_summary: str) -> str:
    """Google's <description> is an HTML blob (often a list of related
    coverage links) - strip it down to plain text."""
    if not html_summary:
        return ""
    soup = BeautifulSoup(html_summary, "html.parser")
    return soup.get_text(separator=" ").strip()


def fetch_top_stories(n: int = 5, hl: str = "en-US", gl: str = "US",
                       ceid: str = "US:en", topic: str = None, query: str = None) -> list:
    """
    Returns a list of up to `n` dicts: {title, source, link, published, summary}

    - Default call -> top stories for the given locale.
    - topic="BUSINESS" / "TECHNOLOGY" / "WORLD" / "SPORTS" / "SCIENCE" / "HEALTH"
      -> that section's top stories.
    - query="artificial intelligence" -> keyword search results instead.
    """
    if query:
        url = f"{BASE_URL}/search?q={quote(query)}&hl={hl}&gl={gl}&ceid={ceid}"
    elif topic:
        url = f"{BASE_URL}/headlines/section/topic/{topic.upper()}?hl={hl}&gl={gl}&ceid={ceid}"
    else:
        url = f"{BASE_URL}?hl={hl}&gl={gl}&ceid={ceid}"

    feed = feedparser.parse(url)
    if getattr(feed, "bozo", False) and not feed.entries:
        raise RuntimeError(f"Could not parse Google News feed at {url}: {feed.bozo_exception}")

    articles = []
    for entry in feed.entries[:n]:
        title = entry.title
        source = None
        # Google usually attaches a <source> tag; fall back to parsing
        # "Headline - Source Name" if it's missing.
        if getattr(entry, "source", None) and getattr(entry.source, "title", None):
            source = entry.source.title
        elif " - " in title:
            title, source = title.rsplit(" - ", 1)

        articles.append({
            "title": title.strip(),
            "source": source or "Unknown",
            "link": entry.get("link", ""),
            "published": entry.get("published", ""),
            "summary": _clean_summary(entry.get("summary", "")),
        })
    return articles


def format_as_digest(articles: list) -> str:
    """
    Combines the articles into a single text block (like a daily digest
    email) so it can be passed straight into
    content_generator.generate_social_content() as one "article".
    """
    lines = ["Top News Today:\n"]
    for i, art in enumerate(articles, 1):
        lines.append(f"{i}. {art['title']} ({art['source']})")
        if art["summary"]:
            lines.append(f"   {art['summary']}")
        lines.append(f"   Source: {art['link']}")
        lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    stories = fetch_top_stories(5)
    print(format_as_digest(stories))

"""Fetches top financial news headlines from NewsAPI or RSS feeds as a fallback."""

import logging
import requests
import feedparser

log = logging.getLogger("news_fetcher")

NEWSAPI_URL = "https://newsapi.org/v2/top-headlines"

# Financial RSS feeds (no API key needed)
RSS_FEEDS = [
    "https://feeds.feedburner.com/marketwatch/topstories",
    "https://www.investing.com/rss/news_25.rss",
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
    "https://feeds.content.dowjones.io/public/rss/SB10001424053111904692904577035732500805476",
    "https://www.ft.com/rss/home",
    "https://seekingalpha.com/market_currents.xml",
]

# Financial keywords for filtering
FINANCIAL_KEYWORDS = [
    "stock", "market", "economy", "GDP", "inflation", "interest rate",
    "Fed", "earnings", "revenue", "merger", "acquisition", "IPO",
    "crypto", "bitcoin", "finance", "investing", "wall street",
    "NASDAQ", "S&P", "Dow Jones", "dividend", "buyback", "bull market",
    "bear market", "recession", "treasury", "bond", "commodity",
]


def fetch_top_headlines(api_key, keywords, categories, max_results=3, exclude_titles=None):
    """Fetches top financial headlines. Tries NewsAPI first, falls back to RSS.

    `exclude_titles` is an optional set of normalized (lowercased, whitespace-
    collapsed) titles to skip — used to stop the same story from being
    reused across same-day runs (e.g. a 9:10am post and a 4:10pm post).
    """
    exclude_titles = exclude_titles or set()

    if api_key:
        headlines = _fetch_from_newsapi(api_key, keywords, categories, max_results, exclude_titles)
        if headlines:
            return headlines
        log.warning("NewsAPI returned no usable results — falling back to RSS.")

    return _fetch_from_rss(max_results, exclude_titles)


def _fetch_from_newsapi(api_key, keywords, categories, max_results, exclude_titles):
    """Fetch financial news from NewsAPI.org."""
    try:
        params = {
            "apiKey": api_key,
            "pageSize": max_results * 6,  # fetch extra so there's room after excluding recent posts
            "sortBy": "publishedAt",  # freshest first — "popularity" tends to return the same story all day
        }
        # Use provided category or default to 'business'
        params["category"] = (categories.split(",")[0].strip() if categories else "business") or "business"
        # Use provided keywords or default to financial terms
        params["q"] = keywords.split(",")[0].strip() if keywords else "stock market"

        resp = requests.get(NEWSAPI_URL, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        articles = data.get("articles", [])

        def _norm(t):
            return " ".join(t.lower().split())

        # Filter for financial relevance, skipping anything already posted recently
        filtered = []
        for a in articles:
            if not a.get("title") or not a.get("url"):
                continue
            if _norm(a["title"]) in exclude_titles:
                continue
            title = (a.get("title", "") + " " + a.get("description", "")).lower()
            if any(kw.lower() in title for kw in FINANCIAL_KEYWORDS):
                filtered.append(
                    {
                        "title": a["title"],
                        "url": a["url"],
                        "source": a.get("source", {}).get("name", "Unknown"),
                        "description": a.get("description", ""),
                        "published_at": a.get("publishedAt", ""),
                    }
                )
            if len(filtered) >= max_results:
                break

        # If filtering removed everything, fall back to the freshest non-excluded
        # articles (still business category) rather than an empty post.
        if not filtered:
            filtered = [
                {
                    "title": a["title"],
                    "url": a["url"],
                    "source": a.get("source", {}).get("name", "Unknown"),
                    "description": a.get("description", ""),
                    "published_at": a.get("publishedAt", ""),
                }
                for a in articles
                if a.get("title") and a.get("url") and _norm(a["title"]) not in exclude_titles
            ][:max_results]

        return filtered

    except Exception as e:
        log.error("NewsAPI error: %s", e)
        return []


def _fetch_from_rss(max_results, exclude_titles=None):
    """Fallback: fetch from financial RSS feeds (no API key needed)."""
    exclude_titles = exclude_titles or set()
    all_entries = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:8]:
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                combined = (title + " " + summary).lower()

                # Filter for financial relevance
                if any(kw in combined for kw in FINANCIAL_KEYWORDS):
                    all_entries.append(
                        {
                            "title": title,
                            "url": entry.get("link", ""),
                            "source": feed.feed.get("title", "RSS"),
                            "description": summary,
                            "published_at": entry.get("published", ""),
                        }
                    )
        except Exception as e:
            log.warning("RSS feed %s error: %s", feed_url, e)

    # Deduplicate by title, and skip anything already posted recently
    seen = set()
    unique = []
    for entry in all_entries:
        key = " ".join(entry["title"].lower().split())
        if key in seen or key in exclude_titles:
            continue
        seen.add(key)
        unique.append(entry)

    return unique[:max_results]

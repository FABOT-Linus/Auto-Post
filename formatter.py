"""Format financial headlines into platform-specific post text.

Uses the proven Hook-Bridge-Value-CTA format for LinkedIn.
Supports a POST_LABEL env var to differentiate morning vs afternoon posts.
"""

import os

MAX_CHARS = {
    "x": 280,
    "facebook": 5000,
    "instagram": 2200,
    "linkedin": 3000,
}


def _get_label():
    """Get the post label from env var, with time-based fallback."""
    label = os.getenv("POST_LABEL", "").strip()
    if label:
        return label
    # Auto-detect based on UTC hour
    from datetime import datetime, timezone
    hour = datetime.now(timezone.utc).hour
    if hour < 15:  # Before 3 PM UTC (~11 AM ET) = morning
        return "☀️ Morning Market Digest"
    else:
        return "🌅 Afternoon Market Close"


def format_posts(headlines):
    """Returns a dict with formatted text for each platform."""
    label = _get_label()
    return {
        "x": _format_x(headlines, label),
        "facebook": _format_facebook(headlines, label),
        "instagram": _format_instagram(headlines, label),
        "linkedin": _format_linkedin(headlines, label),
    }


def _format_x(headlines, label):
    """Short format — X.com has 280 char limit."""
    lines = [f"📊 {label}\n"]
    for i, h in enumerate(headlines, 1):
        line = f"{i}. {h['title']}"
        if len("\n".join(lines + [line])) > 250:
            lines.append("... & more")
            break
        lines.append(line)
    lines.append("\n#MarketNews #Finance #Stocks")
    return "\n".join(lines)


def _format_facebook(headlines, label):
    """Medium format for Facebook — accompanies the image."""
    lines = [f"📊 {label}\n"]
    for h in headlines:
        lines.append(f"• {h['title']}")
        lines.append(f"  Source: {h['source']}")
        lines.append(f"  Read more: {h['url']}\n")
    lines.append("Swipe through the carousel for today's breakdown! ⬅️")
    lines.append("\n#MarketNews #Finance #Stocks #Investing #DailyDigest #BOBNews")
    return "\n".join(lines)


def _format_instagram(headlines, label):
    """Caption for Instagram carousel post."""
    lines = []
    lines.append(f"📊 {label.replace('☀️ ', '').replace('🌅 ', '')} — today's market in 5 slides:\n")
    for i, h in enumerate(headlines, 1):
        lines.append(f"{i}. {h['title']}")
    lines.append("\nSwipe left for the fast breakdown ⬅️")
    lines.append("\n#MarketNews #StockMarket #InvestingDaily #AIInfrastructure #WallStreet #FinancialNews #BOBNews")
    return "\n".join(lines)[:MAX_CHARS["instagram"]]


def _format_linkedin(headlines, label):
    """Hook-Bridge-Value-CTA format for LinkedIn (under 1000 chars)."""
    if not headlines:
        return f"📊 {label} — check back soon for today's headlines."

    # The Hook — derived from the top headline
    top_title = headlines[0]["title"]
    hook = f"{label}: {top_title}\n"

    # The Bridge — context from additional headlines
    if len(headlines) > 1:
        bridge = f"Also moving markets: {headlines[1]['title']}\n"
    else:
        bridge = f"Source: {headlines[0].get('source', 'Financial News')}\n"

    # The Core Value — bullet points
    value_lines = []
    for h in headlines[:4]:
        title = h["title"]
        if len(title) > 80:
            title = title[:77] + "..."
        value_lines.append(f"→ {title}")
    value = "\n".join(value_lines) + "\n"

    # The CTA — open-ended question
    cta = "\nWhat's your read on today's market? Share your take below."

    post = hook + "\n" + bridge + "\n" + value + "\n" + cta
    return post[:MAX_CHARS["linkedin"]]

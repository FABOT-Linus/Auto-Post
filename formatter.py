"""Format financial headlines into platform-specific post text.

Uses the proven Hook-Bridge-Value-CTA format for LinkedIn.
"""

MAX_CHARS = {
    "x": 280,
    "facebook": 5000,
    "instagram": 2200,
    "linkedin": 3000,
}


def format_posts(headlines):
    """Returns a dict with formatted text for each platform."""
    return {
        "x": _format_x(headlines),
        "facebook": _format_facebook(headlines),
        "instagram": _format_instagram(headlines),
        "linkedin": _format_linkedin(headlines),
    }


def _format_x(headlines):
    """Short format — X.com has 280 char limit."""
    lines = ["📊 Daily Market News\n"]
    for i, h in enumerate(headlines, 1):
        line = f"{i}. {h['title']}"
        if len("\n".join(lines + [line])) > 250:
            lines.append("... & more")
            break
        lines.append(line)
    lines.append("\n#MarketNews #Finance #Stocks")
    return "\n".join(lines)


def _format_facebook(headlines):
    """Medium format for Facebook — accompanies the image."""
    lines = ["📊 Daily Market & Financial News Digest\n"]
    for h in headlines:
        lines.append(f"• {h['title']}")
        lines.append(f"  Source: {h['source']}")
        lines.append(f"  Read more: {h['url']}\n")
    lines.append("Swipe through the carousel for today's breakdown! ⬅️")
    lines.append("\n#MarketNews #Finance #Stocks #Investing #DailyDigest #BOBNews")
    return "\n".join(lines)


def _format_instagram(headlines):
    """Caption for Instagram carousel post."""
    lines = []
    # Summary paragraph
    lines.append("📊 Today's market in 5 slides:\n")
    for i, h in enumerate(headlines, 1):
        lines.append(f"{i}. {h['title']}")
    lines.append("\nSwipe left for the fast breakdown ⬅️")
    lines.append("\n#MarketNews #StockMarket #InvestingDaily #AIInfrastructure #WallStreet #FinancialNews #BOBNews")
    return "\n".join(lines)[:MAX_CHARS["instagram"]]


def _format_linkedin(headlines):
    """Hook-Bridge-Value-CTA format for LinkedIn (under 1000 chars)."""
    if not headlines:
        return "📊 Daily market news — check back soon for today's headlines."

    # The Hook — derived from the top headline
    top_title = headlines[0]["title"]
    hook = f"{top_title}\n"

    # The Bridge — context from additional headlines
    if len(headlines) > 1:
        bridge = f"Also moving markets today: {headlines[1]['title']}\n"
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

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
    # The Hook — bold, scroll-stopping
    hook = "AI isn't just moving markets anymore — it's rewriting the entire playbook.\n"

    # The Bridge — why it matters now
    bridge = "Wall Street posted fresh gains as AI infrastructure earnings beat expectations and cooling inflation data reinforced bets that the Fed holds rates steady.\n"

    # The Core Value — bullet points
    value_lines = []
    for h in headlines[:4]:
        # Shorten title for readability
        title = h["title"]
        if len(title) > 80:
            title = title[:77] + "..."
        value_lines.append(f"→ {title}")
    value = "\n".join(value_lines) + "\n"

    # The CTA — open-ended question
    cta = "\nAre we watching the start of a new market cycle, or another bubble waiting to pop?"

    post = hook + "\n" + bridge + "\n" + value + "\n" + cta
    return post[:MAX_CHARS["linkedin"]]

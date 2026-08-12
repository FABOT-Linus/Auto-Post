"""Formats financial headlines into platform-specific post text."""

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
    """Medium format for Facebook."""
    lines = ["📊 Daily Market & Financial News Digest\n"]
    for h in headlines:
        lines.append(f"• {h['title']}")
        lines.append(f"  Source: {h['source']}")
        lines.append(f"  Read more: {h['url']}\n")
    lines.append("#MarketNews #Finance #Stocks #Investing #DailyDigest")
    return "\n".join(lines)


def _format_instagram(headlines):
    """Caption for Instagram (image is generated separately)."""
    lines = ["📊 Daily Market News Digest\n"]
    for i, h in enumerate(headlines, 1):
        lines.append(f"{i}. {h['title']}")
    lines.append("\nLink in bio for full stories!")
    lines.append("\n#MarketNews #Finance #Stocks #Investing #DailyDigest #WallStreet")
    return "\n".join(lines)[:MAX_CHARS["instagram"]]


def _format_linkedin(headlines):
    """Professional format for LinkedIn."""
    lines = ["📊 Daily Financial Markets News Digest\n"]
    for h in headlines:
        lines.append(f"• {h['title']}")
        lines.append(f"  Source: {h['source']}")
        lines.append(f"  {h['url']}\n")
    lines.append("Follow for daily market updates!")
    lines.append("\n#Finance #Markets #Investing #StockMarket #Economy #DailyDigest")
    return "\n".join(lines)[:MAX_CHARS["linkedin"]]

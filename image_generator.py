"""Generate bold eye-catching news card images for social media.

Auto-detects market mood (bull/bear/neutral) from headlines and generates
a matching style: big headline, checklist bullets, icon, CTA bar.

Bull  = green, "MARKET UPDATE",  bull icon
Bear  = red,   "MARKET PULLBACK", bear icon
Neutral = gold, "EARNINGS SPOTLIGHT", chart icon

Icon PNGs (bull.png, bear.png, chart.png) are loaded from the same directory
if available; otherwise simple vector icons are drawn with PIL.
"""

import os
import io
import re
import logging
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

log = logging.getLogger("image_generator")

WIDTH, HEIGHT = 1080, 1080

# --- Mood keywords ---
BULL_KEYWORDS = [
    "rally", "rallies", "surge", "surges", "surging", "gain", "gains", "gained",
    "rise", "rises", "rising", "soar", "soars", "soaring", "jump", "jumps",
    "jumped", "climb", "climbs", "climbing", "rally", "rebound", "rebounds",
    "rebounded", "beat", "beats", "beats expectations", "upgrade", "upgraded",
    "bullish", "optimism", "optimistic", "cools", "cooled", "inflation cools",
    "rally", "up", "higher", "record high", "all-time high", "breakthrough",
]

BEAR_KEYWORDS = [
    "slide", "slides", "slump", "slumps", "drop", "drops", "dropped", "fall",
    "falls", "falling", "fell", "plunge", "plunges", "plunging", "tumble",
    "tumbles", "tumbling", "decline", "declines", "declining", "sink", "sinks",
    "sinking", "sank", "crash", "crashes", "crashing", "sell-off", "selloff",
    "loss", "losses", "bearish", "pessimism", "pessimistic", "down", "lower",
    "rate fears", "spike", "spikes", "resistance", "hit resistance", "warns",
    "warning", "concern", "concerns", "fear", "fears", "threat", "threaten",
]

NEUTRAL_KEYWORDS = [
    "earnings", "earnings season", "revenue", "guidance", "quarterly",
    "quarter", "results", "q1", "q2", "q3", "q4", "analyst", "analysts",
    "price target", "forecast", "outlook", "estimate", "estimates",
    "report", "reports", "reported", "review", "preview", "watch",
    "check", "checks", "what to watch", "in focus",
]


def _detect_mood(headlines):
    """Detect market mood from headline text. Returns 'bull', 'bear', or 'neutral'."""
    text = " ".join(h.get("title", "") for h in headlines).lower()

    bull_score = sum(1 for kw in BULL_KEYWORDS if kw in text)
    bear_score = sum(1 for kw in BEAR_KEYWORDS if kw in text)
    neutral_score = sum(1 for kw in NEUTRAL_KEYWORDS if kw in text)

    log.info("Mood scores — bull=%d bear=%d neutral=%d", bull_score, bear_score, neutral_score)

    scores = {"bull": bull_score, "bear": bear_score, "neutral": neutral_score}
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "bull"  # default to bull when no keywords match
    return best


# --- Mood styles ---
MOOD_STYLES = {
    "bull": {
        "accent": (60, 220, 100),       # green
        "headline_main": "MARKET",
        "headline_sub": "UPDATE",
        "icon_file": "bull.png",
    },
    "bear": {
        "accent": (235, 70, 70),        # red
        "headline_main": "MARKET",
        "headline_sub": "PULLBACK",
        "icon_file": "bear.png",
    },
    "neutral": {
        "accent": (255, 193, 50),       # gold
        "headline_main": "EARNINGS",
        "headline_sub": "SPOTLIGHT",
        "icon_file": "chart.png",
    },
}


def _load_font(size, bold=False):
    """Load a font with fallback."""
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def _wrap_text(draw, text, font, max_width):
    """Wrap text to fit within max_width."""
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _try_load_icon(filename):
    """Try to load icon PNG from same directory as this script. Returns None if not found."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(script_dir, filename)
    if os.path.exists(icon_path):
        try:
            img = Image.open(icon_path).convert("RGBA")
            log.info("Loaded icon: %s", icon_path)
            return img
        except Exception as e:
            log.warning("Could not load icon %s: %s", icon_path, e)
    return None


def _draw_bull_icon(draw, x, y, size, color):
    """Draw a simple bull silhouette with PIL primitives."""
    # Body
    draw.ellipse([x, y + size*0.2, x + size, y + size*0.8], outline=color, width=4)
    # Head
    draw.ellipse([x + size*0.6, y, x + size*1.1, y + size*0.4], outline=color, width=4)
    # Horns
    draw.arc([x + size*0.75, y - size*0.05, x + size*0.95, y + size*0.15], 200, 340, fill=color, width=4)
    draw.arc([x + size*0.95, y - size*0.05, x + size*1.15, y + size*0.15], 200, 340, fill=color, width=4)
    # Up arrow
    draw.line([x + size*0.3, y + size*0.9, x + size*0.3, y + size*1.15], fill=color, width=5)
    draw.polygon([
        (x + size*0.3, y + size*0.85),
        (x + size*0.15, y + size*1.0),
        (x + size*0.45, y + size*1.0),
    ], fill=color)


def _draw_bear_icon(draw, x, y, size, color):
    """Draw a simple bear silhouette with PIL primitives."""
    # Body
    draw.ellipse([x, y + size*0.25, x + size, y + size*0.85], outline=color, width=4)
    # Head
    draw.ellipse([x + size*0.6, y + size*0.05, x + size*1.05, y + size*0.45], outline=color, width=4)
    # Ears
    draw.ellipse([x + size*0.62, y - size*0.02, x + size*0.78, y + size*0.14], outline=color, width=3)
    draw.ellipse([x + size*0.88, y - size*0.02, x + size*1.04, y + size*0.14], outline=color, width=3)
    # Down arrow
    draw.line([x + size*0.3, y + size*0.9, x + size*0.3, y + size*1.15], fill=color, width=5)
    draw.polygon([
        (x + size*0.3, y + size*1.2),
        (x + size*0.15, y + size*1.05),
        (x + size*0.45, y + size*1.05),
    ], fill=color)


def _draw_chart_icon(draw, x, y, size, color):
    """Draw a simple chart/magnifying glass with PIL primitives."""
    # Bars
    bar_w = size * 0.08
    for i, h in enumerate([0.3, 0.5, 0.4, 0.7, 0.55]):
        bx = x + i * (bar_w * 2.5)
        draw.rectangle([bx, y + size * (1 - h), bx + bar_w, y + size], fill=color)
    # Trend line
    points = [
        (x + bar_w * 0.5, y + size * 0.7),
        (x + bar_w * 3, y + size * 0.5),
        (x + bar_w * 5.5, y + size * 0.6),
        (x + bar_w * 8, y + size * 0.3),
        (x + bar_w * 10.5, y + size * 0.45),
    ]
    for i in range(len(points) - 1):
        draw.line([points[i], points[i + 1]], fill=color, width=4)
    # Magnifying glass circle
    cx, cy = x + size * 0.75, y + size * 0.35
    r = size * 0.2
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=4)
    # Handle
    draw.line([cx + r * 0.7, cy + r * 0.7, cx + r * 1.3, cy + r * 1.3], fill=color, width=5)


def _draw_icon_for_mood(draw, mood, x, y, size, color):
    """Draw a simple fallback icon based on mood."""
    if mood == "bull":
        _draw_bull_icon(draw, x, y, size, color)
    elif mood == "bear":
        _draw_bear_icon(draw, x, y, size, color)
    else:
        _draw_chart_icon(draw, x, y, size, color)


def generate_news_image(headlines, platform="generic"):
    """
    Generate a bold news card image from headlines.
    Auto-detects market mood and picks the matching style.

    Args:
        headlines: list of dicts with 'title', 'source', 'url' keys
        platform: 'facebook', 'instagram', 'linkedin', or 'generic'

    Returns:
        BytesIO buffer containing JPEG image data
    """
    mood = _detect_mood(headlines)
    style = MOOD_STYLES[mood]
    accent = style["accent"]

    log.info("Detected mood: %s — using style: %s / %s",
             mood, style["headline_main"], style["headline_sub"])

    # Base canvas — solid near-black
    img = Image.new("RGB", (WIDTH, HEIGHT), (10, 10, 12))
    draw = ImageDraw.Draw(img)

    # --- Try to load icon PNG, or draw fallback ---
    icon_img = _try_load_icon(style["icon_file"])
    if icon_img:
        icon_w = 560
        icon_h = int(icon_img.height * (icon_w / icon_img.width))
        # Use compatible resampling filter for different Pillow versions
        try:
            resampling = Image.Resampling.LANCZOS
        except AttributeError:
            resampling = Image.LANCZOS
        icon_img = icon_img.resize((icon_w, icon_h), resampling)
        paste_x = WIDTH - icon_w + 60
        paste_y = HEIGHT - icon_h - 130
        # Create a temp RGBA image for pasting with alpha
        img_rgba = img.convert("RGBA")
        img_rgba.alpha_composite(icon_img, (paste_x, paste_y))
        img = img_rgba.convert("RGB")
        draw = ImageDraw.Draw(img)
    else:
        # Draw a simple vector icon on the right side
        _draw_icon_for_mood(draw, mood, 650, 350, 350, accent)

    # --- Black gradient overlay for text legibility ---
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)
    for x in range(WIDTH):
        if x < 750:
            alpha = 255
        elif x < 950:
            alpha = int(255 * (1 - (x - 750) / 200))
        else:
            alpha = 0
        odraw.line([(x, 0), (x, HEIGHT)], fill=(10, 10, 12, alpha))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    draw = ImageDraw.Draw(img)

    # --- Fonts ---
    brand_font = _load_font(26, bold=True)
    headline_font = _load_font(68, bold=True)
    subtitle_font = _load_font(30, bold=True)
    bullet_font = _load_font(28, bold=False)
    cta_font = _load_font(26, bold=True)

    # --- Brand top-left ---
    draw.text((60, 50), "BOB", fill=(255, 255, 255), font=brand_font)
    bbox = draw.textbbox((0, 0), "BOB", font=brand_font)
    draw.text((60 + bbox[2] - bbox[0], 50), "NEWS", fill=accent, font=brand_font)

    # --- Big headline ---
    draw.text((60, 120), style["headline_main"], fill=(255, 255, 255), font=headline_font)
    draw.text((60, 195), style["headline_sub"], fill=accent, font=headline_font)

    # --- Subtitle ---
    # Use POST_IMAGE_SUBTITLE env var for morning vs afternoon label
    import os as _os
    _img_subtitle = _os.getenv("POST_IMAGE_SUBTITLE", "").strip() or "WHAT YOU NEED TO KNOW"
    draw.text((60, 295), _img_subtitle.upper(), fill=(200, 205, 210), font=subtitle_font)

    # --- Bullet checklist from headlines ---
    bullet_y = 375
    for h in headlines[:4]:
        title = h.get("title", "")
        # Checkmark circle
        draw.ellipse([60, bullet_y, 90, bullet_y + 30], outline=accent, width=3)
        draw.line([68, bullet_y + 15, 76, bullet_y + 23], fill=accent, width=3)
        draw.line([76, bullet_y + 23, 84, bullet_y + 7], fill=accent, width=3)

        # Wrap headline text
        lines = _wrap_text(draw, title, bullet_font, 600)
        ty = bullet_y
        for line in lines[:2]:
            draw.text((105, ty), line, fill=(235, 235, 240), font=bullet_font)
            ty += 34
        bullet_y += max(52, len(lines[:2]) * 34 + 14)

    # --- CTA bar ---
    cta_h = 90
    draw.rectangle([0, HEIGHT - cta_h, WIDTH, HEIGHT], fill=accent)
    cta_text = "STAY INFORMED. STAY AHEAD."
    bbox = draw.textbbox((0, 0), cta_text, font=cta_font)
    draw.text((60, HEIGHT - cta_h + (cta_h - (bbox[3] - bbox[1])) // 2 - 5), cta_text, fill=(10, 10, 12), font=cta_font)

    # Handle on right of CTA bar
    handle = "@BOBNewsDailyPost"
    bbox2 = draw.textbbox((0, 0), handle, font=cta_font)
    draw.text((WIDTH - 60 - (bbox2[2] - bbox2[0]), HEIGHT - cta_h + (cta_h - (bbox2[3] - bbox2[1])) // 2 - 5),
              handle, fill=(10, 10, 12), font=cta_font)

    # Convert to bytes
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    buf.seek(0)
    return buf


def generate_story_image(headlines, platform="generic"):
    """Placeholder for vertical story format (1080x1920). Not yet implemented."""
    pass

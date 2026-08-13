"""Generate professional eye-catching news card images for social media.

Creates a polished 1080x1080 image with:
- BOBNews branding header with gradient
- Today's date
- Headline cards with numbered badges
- Source attribution
- Professional footer with social handles
"""

import os
import io
import logging
import textwrap
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageFilter

log = logging.getLogger("image_generator")

# --- Design constants ---
WIDTH, HEIGHT = 1080, 1080

# Color palette — professional financial news look
BG_TOP = (8, 15, 35)           # Deep navy
BG_BOTTOM = (20, 28, 55)       # Slightly lighter navy
ACCENT = (0, 200, 255)          # Bright cyan for branding
ACCENT_GOLD = (255, 193, 7)     # Gold for numbers/badges
CARD_BG = (30, 38, 68)          # Card background
CARD_BORDER = (50, 60, 95)      # Card border
TEXT_PRIMARY = (255, 255, 255)  # White headlines
TEXT_SECONDARY = (180, 190, 210)  # Gray for sources
TEXT_MUTED = (120, 130, 155)    # Muted gray for footer
HEADER_GRADIENT = (15, 80, 180) # Header bar gradient


def _load_font(size, bold=False):
    """Load a font with fallback."""
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except (IOError, OSError):
            continue
    return ImageFont.load_default()


def _draw_gradient_background(img, top_color, bottom_color):
    """Draw a vertical gradient background."""
    width, height = img.size
    for y in range(height):
        ratio = y / height
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
        img.putpixel((0, y), (r, g, b))
    # Copy the single column across the whole image
    for x in range(1, width):
        for y in range(height):
            img.putpixel((x, y), img.getpixel((0, y)))


def _draw_gradient_rect(draw, x0, y0, x1, y1, top_color, bottom_color):
    """Draw a vertical gradient rectangle."""
    for y in range(y0, y1):
        ratio = (y - y0) / max(1, y1 - y0)
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
        draw.line([(x0, y), (x1, y)], fill=(r, g, b))


def _rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    """Draw a rounded rectangle."""
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def _wrap_text(draw, text, font, max_width):
    """Wrap text to fit within max_width, returns list of lines."""
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


def generate_news_image(headlines, platform="generic"):
    """
    Generate a professional news card image from headlines.
    
    Args:
        headlines: list of dicts with 'title', 'source', 'url' keys
        platform: 'facebook', 'instagram', 'linkedin', or 'generic'
    
    Returns:
        BytesIO buffer containing JPEG image data
    """
    img = Image.new("RGB", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(img)

    # --- Background gradient ---
    _draw_gradient_background(img, BG_TOP, BG_BOTTOM)
    draw = ImageDraw.Draw(img)

    # --- Fonts ---
    brand_font = _load_font(42, bold=True)
    date_font = _load_font(24, bold=False)
    headline_font = _load_font(30, bold=True)
    source_font = _load_font(22, bold=False)
    number_font = _load_font(28, bold=True)
    footer_font = _load_font(24, bold=False)
    tagline_font = _load_font(20, bold=False)

    # --- Header bar ---
    header_height = 130
    _draw_gradient_rect(draw, 0, 0, WIDTH, header_height, (12, 25, 60), (20, 40, 90))

    # Header accent line
    draw.rectangle([0, header_height, WIDTH, header_height + 4], fill=ACCENT)

    # Brand name with accent dot
    draw.text((50, 30), "BOB", fill=(255, 255, 255), font=brand_font)
    bbox = draw.textbbox((0, 0), "BOB", font=brand_font)
    bob_width = bbox[2] - bbox[0]
    draw.text((50 + bob_width, 30), "News", fill=ACCENT, font=brand_font)

    # Date on the right
    today = datetime.now().strftime("%B %d, %Y")
    bbox = draw.textbbox((0, 0), today, font=date_font)
    date_width = bbox[2] - bbox[0]
    draw.text((WIDTH - 50 - date_width, 40), today, fill=TEXT_SECONDARY, font=date_font)

    # "DAILY MARKET DIGEST" tagline
    tagline = "DAILY MARKET DIGEST"
    bbox = draw.textbbox((0, 0), tagline, font=tagline_font)
    tagline_width = bbox[2] - bbox[0]
    draw.text((WIDTH - 50 - tagline_width, 75), tagline, fill=ACCENT, font=tagline_font)

    # --- Headline cards ---
    card_start_y = header_height + 40
    card_height = 230
    card_margin = 50
    card_width = WIDTH - 2 * card_margin
    card_gap = 20

    for i, headline in enumerate(headlines[:3]):
        card_y = card_start_y + i * (card_height + card_gap)

        # Card background
        _rounded_rect(
            draw,
            [card_margin, card_y, card_margin + card_width, card_y + card_height],
            radius=20,
            fill=CARD_BG,
            outline=CARD_BORDER,
            width=2,
        )

        # Number badge (gold circle)
        badge_size = 50
        badge_x = card_margin + 25
        badge_y = card_y + 25
        draw.ellipse(
            [badge_x, badge_y, badge_x + badge_size, badge_y + badge_size],
            fill=ACCENT_GOLD,
        )
        num_text = str(i + 1)
        bbox = draw.textbbox((0, 0), num_text, font=number_font)
        num_w = bbox[2] - bbox[0]
        num_h = bbox[3] - bbox[1]
        draw.text(
            (badge_x + (badge_size - num_w) / 2, badge_y + (badge_size - num_h) / 2 - 2),
            num_text,
            fill=(20, 20, 30),
            font=number_font,
        )

        # Headline text (wrapped)
        text_x = badge_x + badge_size + 25
        text_max_width = card_margin + card_width - text_x - 30
        headline_lines = _wrap_text(draw, headline["title"], headline_font, text_max_width)

        line_y = card_y + 30
        for line in headline_lines[:4]:  # Max 4 lines per card
            draw.text((text_x, line_y), line, fill=TEXT_PRIMARY, font=headline_font)
            line_y += 38

        # Source
        source_text = f"Source: {headline.get('source', 'Unknown')}"
        draw.text(
            (text_x, card_y + card_height - 45),
            source_text,
            fill=TEXT_SECONDARY,
            font=source_font,
        )

        # Accent bar on left side of card
        draw.rectangle(
            [card_margin, card_y + 15, card_margin + 5, card_y + card_height - 15],
            fill=ACCENT,
        )

    # --- Footer ---
    footer_y = HEIGHT - 80

    # Footer accent line
    draw.rectangle([50, footer_y - 20, WIDTH - 50, footer_y - 18], fill=CARD_BORDER)

    # Social handles
    handles = "@BOBNewsDailyPost"
    bbox = draw.textbbox((0, 0), handles, font=footer_font)
    handles_width = bbox[2] - bbox[0]
    draw.text((50, footer_y), handles, fill=ACCENT, font=footer_font)

    # Hashtags on the right
    hashtags = "#MarketNews #Finance #Investing"
    bbox = draw.textbbox((0, 0), hashtags, font=footer_font)
    tags_width = bbox[2] - bbox[0]
    draw.text((WIDTH - 50 - tags_width, footer_y), hashtags, fill=TEXT_MUTED, font=footer_font)

    # Convert to bytes
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    buf.seek(0)
    return buf


def generate_story_image(headlines, platform="generic"):
    """
    Generate a 1080x1920 story/vertical format image (for Instagram stories, etc).
    Currently unused but available for future enhancement.
    """
    pass

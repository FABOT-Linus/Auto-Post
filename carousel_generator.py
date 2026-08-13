"""Generate Instagram carousel slides — 5-slide Hook-Data-Impact-CTA format.

Slide 1: Bold hook headline (3-6 words, high contrast)
Slide 2-3: One key stat/fact per slide
Slide 4: The impact — why it matters today
Slide 5: CTA — save/share prompt
"""

import os
import io
import logging
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

log = logging.getLogger("carousel_generator")

WIDTH, HEIGHT = 1080, 1350  # Instagram portrait carousel

# Colors
BG_TOP = (8, 15, 35)
BG_BOTTOM = (20, 28, 55)
ACCENT = (0, 200, 255)
ACCENT_GOLD = (255, 193, 7)
ACCENT_GREEN = (0, 230, 118)
TEXT_WHITE = (255, 255, 255)
TEXT_GRAY = (180, 190, 210)
TEXT_MUTED = (120, 130, 155)
CARD_BG = (30, 38, 68)
CARD_BORDER = (50, 60, 95)


def _load_font(size, bold=False):
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
    width, height = img.size
    for y in range(height):
        ratio = y / height
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
        for x in range(width):
            img.putpixel((x, y), (r, g, b))


def _wrap_text(draw, text, font, max_width):
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


def _center_text(draw, text, font, y, width, color):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (width - text_width) / 2
    draw.text((x, y), text, fill=color, font=font)
    return text_width


def _slide_base(slide_num, total=5):
    """Create a base image with gradient and page indicator."""
    img = Image.new("RGB", (WIDTH, HEIGHT))
    _draw_gradient_background(img, BG_TOP, BG_BOTTOM)
    draw = ImageDraw.Draw(img)

    # Top accent bar
    draw.rectangle([0, 0, WIDTH, 6], fill=ACCENT)

    # BOBNews branding top left
    brand_font = _load_font(28, bold=True)
    draw.text((50, 25), "BOB", fill=TEXT_WHITE, font=brand_font)
    bbox = draw.textbbox((0, 0), "BOB", font=brand_font)
    draw.text((50 + bbox[2] - bbox[0], 25), "News", fill=ACCENT, font=brand_font)

    # Date top right
    date_font = _load_font(20)
    today = datetime.now().strftime("%B %d, %Y")
    bbox = draw.textbbox((0, 0), today, font=date_font)
    draw.text((WIDTH - 50 - (bbox[2] - bbox[0]), 30), today, fill=TEXT_GRAY, font=date_font)

    # Page dots bottom
    dot_y = HEIGHT - 50
    dot_spacing = 18
    total_dots_width = (total - 1) * dot_spacing
    start_x = (WIDTH - total_dots_width) / 2
    for i in range(total):
        dot_x = start_x + i * dot_spacing
        color = ACCENT if i == slide_num - 1 else TEXT_MUTED
        r = 5 if i == slide_num - 1 else 3
        draw.ellipse([dot_x - r, dot_y - r, dot_x + r, dot_y + r], fill=color)

    return img, ImageDraw.Draw(img)


def generate_slide_1():
    """Slide 1: Bold hook headline."""
    img, draw = _slide_base(1)

    # Big bold text — 3-6 words
    hook_font = _load_font(72, bold=True)
    sub_font = _load_font(36, bold=False)

    lines = ["AI JUST", "REWROTE", "THE MARKETS"]

    y = 450
    for line in lines:
        _center_text(draw, line, hook_font, y, WIDTH, ACCENT_GOLD)
        y += 90

    # Subtitle
    y += 40
    _center_text(draw, "Today's market breakdown", sub_font, y, WIDTH, TEXT_GRAY)

    # Swipe indicator
    swipe_font = _load_font(22)
    _center_text(draw, "Swipe left →", swipe_font, HEIGHT - 120, WIDTH, ACCENT)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    buf.seek(0)
    return buf


def generate_slide_2(headlines):
    """Slide 2: Key stat 1 — AI infrastructure earnings."""
    img, draw = _slide_base(2)

    stat_font = _load_font(56, bold=True)
    detail_font = _load_font(32, bold=False)
    source_font = _load_font(24)

    # Big stat
    _center_text(draw, "AI INFRA", stat_font, 300, WIDTH, ACCENT_GREEN)

    _center_text(draw, "SURGES", stat_font, 370, WIDTH, ACCENT_GREEN)

    # Detail
    y = 500
    lines = _wrap_text(draw, "CoreWeave & Supermicro earnings beat expectations", detail_font, WIDTH - 120)
    for line in lines:
        _center_text(draw, line, detail_font, y, WIDTH, TEXT_WHITE)
        y += 45

    y += 30
    lines = _wrap_text(draw, "→ AI infrastructure stocks jumping on real revenue", detail_font, WIDTH - 120)
    for line in lines:
        _center_text(draw, line, detail_font, y, WIDTH, TEXT_GRAY)
        y += 45

    # Source
    _center_text(draw, "Source: Yahoo Finance", source_font, HEIGHT - 130, WIDTH, TEXT_MUTED)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    buf.seek(0)
    return buf


def generate_slide_3(headlines):
    """Slide 3: Key stat 2 — Goldman Sachs acquisition."""
    img, draw = _slide_base(3)

    stat_font = _load_font(56, bold=True)
    detail_font = _load_font(32, bold=False)
    source_font = _load_font(24)

    # Big stat
    _center_text(draw, "$2.3 BILLION", stat_font, 300, WIDTH, ACCENT_GOLD)

    _center_text(draw, "ACQUISITION", stat_font, 370, WIDTH, ACCENT_GOLD)

    # Detail
    y = 500
    lines = _wrap_text(draw, "Goldman Sachs to buy ETF provider Neos", detail_font, WIDTH - 120)
    for line in lines:
        _center_text(draw, line, detail_font, y, WIDTH, TEXT_WHITE)
        y += 45

    y += 30
    lines = _wrap_text(draw, "→ Major bet on structured products space", detail_font, WIDTH - 120)
    for line in lines:
        _center_text(draw, line, detail_font, y, WIDTH, TEXT_GRAY)
        y += 45

    # Source
    _center_text(draw, "Source: Yahoo Finance", source_font, HEIGHT - 130, WIDTH, TEXT_MUTED)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    buf.seek(0)
    return buf


def generate_slide_4():
    """Slide 4: The Impact."""
    img, draw = _slide_base(4)

    title_font = _load_font(48, bold=True)
    body_font = _load_font(34, bold=False)
    highlight_font = _load_font(34, bold=True)

    _center_text(draw, "THE IMPACT", title_font, 280, WIDTH, ACCENT)

    y = 400
    lines = _wrap_text(draw, "Cooling inflation + AI earnings", body_font, WIDTH - 120)
    for line in lines:
        _center_text(draw, line, body_font, y, WIDTH, TEXT_WHITE)
        y += 50

    y += 20
    _center_text(draw, "=", highlight_font, y, WIDTH, ACCENT_GOLD)
    y += 60

    lines = _wrap_text(draw, "Fed likely holds rates", highlight_font, WIDTH - 120)
    for line in lines:
        _center_text(draw, line, highlight_font, y, WIDTH, ACCENT_GREEN)
        y += 50

    y += 30
    lines = _wrap_text(draw, "Markets have room to run", body_font, WIDTH - 120)
    for line in lines:
        _center_text(draw, line, body_font, y, WIDTH, TEXT_WHITE)
        y += 45

    y += 10
    lines = _wrap_text(draw, "— but for how long?", body_font, WIDTH - 120)
    for line in lines:
        _center_text(draw, line, body_font, y, WIDTH, TEXT_GRAY)
        y += 45

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    buf.seek(0)
    return buf


def generate_slide_5():
    """Slide 5: CTA — save/share."""
    img, draw = _slide_base(5)

    title_font = _load_font(52, bold=True)
    body_font = _load_font(32, bold=False)

    _center_text(draw, "STAY AHEAD", title_font, 400, WIDTH, ACCENT)

    y = 500
    _center_text(draw, "Save this post", body_font, y, WIDTH, TEXT_WHITE)
    y += 50
    _center_text(draw, "to keep up with", body_font, y, WIDTH, TEXT_WHITE)
    y += 50
    _center_text(draw, "the markets", body_font, y, WIDTH, TEXT_WHITE)

    y += 80
    _center_text(draw, "Share with a colleague", body_font, y, WIDTH, ACCENT)

    # Handle
    handle_font = _load_font(26, bold=True)
    _center_text(draw, "@BOBNewsDailyPost", handle_font, HEIGHT - 130, WIDTH, ACCENT)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    buf.seek(0)
    return buf


def generate_all_slides(headlines):
    """Generate all 5 carousel slides. Returns list of BytesIO buffers."""
    return [
        generate_slide_1(),
        generate_slide_2(headlines),
        generate_slide_3(headlines),
        generate_slide_4(),
        generate_slide_5(),
    ]


if __name__ == "__main__":
    # Preview mode — save all slides as files
    headlines = [
        {"title": "Wall St gains as AI earnings lift tech", "source": "Yahoo Finance"},
        {"title": "AI infrastructure stocks surge", "source": "Yahoo Finance"},
        {"title": "Goldman Sachs to buy ETF provider Neos in $2.3 billion deal", "source": "Yahoo Finance"},
    ]
    slides = generate_all_slides(headlines)
    for i, slide in enumerate(slides, 1):
        with open(f"carousel_slide_{i}.jpg", "wb") as f:
            f.write(slide.getvalue())
        print(f"Slide {i} saved ({len(slide.getvalue())} bytes)")

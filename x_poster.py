"""Post to X.com (Twitter) via API v2 using tweepy.

Supports two modes:
- TEXT mode: posts a text-only tweet (default)
- IMAGE mode: generates an image card from the headline and posts it with the tweet
  (set ENABLE_X_IMAGE=true in .env or GitHub variable)
"""

import os
import io
import logging
import tweepy
import requests
from PIL import Image, ImageDraw, ImageFont

log = logging.getLogger("x_poster")


def post_to_x(text, headlines=None):
    """Posts to X.com. If ENABLE_X_IMAGE=true and headlines provided, posts with image."""
    try:
        client = tweepy.Client(
            consumer_key=os.getenv("X_API_KEY"),
            consumer_secret=os.getenv("X_API_SECRET"),
            access_token=os.getenv("X_ACCESS_TOKEN"),
            access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET"),
        )

        image_mode = os.getenv("ENABLE_X_IMAGE", "false").lower() == "true"

        if image_mode and headlines:
            # --- Post with image ---
            media_id = _upload_media(client, headlines)
            if media_id:
                response = client.create_tweet(text=text, media_ids=[media_id])
            else:
                log.warning("Image generation failed — falling back to text-only.")
                response = client.create_tweet(text=text)
        else:
            # --- Text-only post ---
            response = client.create_tweet(text=text)

        tweet_id = response.data["id"]
        log.info("Posted to X.com — tweet ID: %s (image: %s)", tweet_id, image_mode)
        return {"success": True, "tweet_id": tweet_id, "image": image_mode}

    except Exception as e:
        log.error("X.com post failed: %s", e)
        return {"success": False, "error": str(e)}


def _upload_media(client, headlines):
    """Generates an image card and uploads it to X.com. Returns media_id."""
    try:
        image_bytes = _generate_image_card(headlines)

        # Use tweepy's API v1.1 for media upload (v2 doesn't support media upload yet)
        auth = tweepy.OAuth1UserHandler(
            os.getenv("X_API_KEY"),
            os.getenv("X_API_SECRET"),
            os.getenv("X_ACCESS_TOKEN"),
            os.getenv("X_ACCESS_TOKEN_SECRET"),
        )
        api = tweepy.API(auth)

        # Save temp file and upload
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            image_bytes.seek(0)
            tmp.write(image_bytes.read())
            tmp_path = tmp.name

        media = api.media_upload(tmp_path)
        os.unlink(tmp_path)

        log.info("Uploaded image to X.com — media ID: %s", media.media_id)
        return media.media_id

    except Exception as e:
        log.error("X.com image upload failed: %s", e)
        return None


def _generate_image_card(headlines):
    """Generates a 1200x675 image card with financial news headlines."""
    width, height = 1200, 675
    bg_color = (15, 23, 35)        # Dark navy
    text_color = (255, 255, 255)
    accent_color = (0, 200, 150)    # Green accent (finance vibe)
    source_color = (150, 160, 175)

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Fonts — try Linux paths first, then Windows
    font_paths = [
        ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        ("C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/arial.ttf"),
    ]
    title_font = body_font = source_font = ImageFont.load_default()
    for bold_path, regular_path in font_paths:
        try:
            title_font = ImageFont.truetype(bold_path, 42)
            body_font = ImageFont.truetype(regular_path, 26)
            source_font = ImageFont.truetype(regular_path, 18)
            break
        except (IOError, OSError):
            continue

    # Header bar
    draw.rectangle([0, 0, width, 80], fill=(0, 200, 150))
    draw.text((40, 20), "📊 DAILY MARKET NEWS", fill=(15, 23, 35), font=title_font)

    # Headlines
    y = 110
    for i, h in enumerate(headlines, 1):
        # Number badge
        draw.ellipse([40, y, 70, y + 30], fill=accent_color)
        draw.text((48, y + 3), str(i), fill=bg_color, font=source_font)

        # Headline text (wrapped)
        lines = _wrap_text(draw, h["title"], body_font, width - 120)
        for line in lines:
            draw.text((85, y), line, fill=text_color, font=body_font)
            y += 32

        # Source
        draw.text((85, y + 2), f"Source: {h['source']}", fill=source_color, font=source_font)
        y += 35

        if y > height - 60:
            break

    # Footer
    draw.text((40, height - 35), "#MarketNews #Finance #DailyDigest", fill=accent_color, font=source_font)

    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    buf.seek(0)
    return buf


def _wrap_text(draw, text, font, max_width):
    """Wraps text to fit within max_width."""
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

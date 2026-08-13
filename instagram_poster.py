"""Post to Instagram Business account via the Instagram Graph API.

Instagram does NOT support text-only posts. This module generates
a simple image card from the first headline using Pillow, uploads it,
and publishes it.

Image hosting: uses tmpfiles.org (free, no API key required).
Fallback: 0x0.st if tmpfiles.org is unavailable.
"""

import os
import io
import time
import logging
import requests
from PIL import Image, ImageDraw, ImageFont

log = logging.getLogger("instagram_poster")

IG_GRAPH_URL = "https://graph.facebook.com/v19.0"


def post_to_instagram(caption, headlines):
    """Generates an image card and posts to Instagram. Returns dict with success/status."""
    try:
        access_token = os.getenv("IG_ACCESS_TOKEN") or os.getenv("FACEBOOK_ACCESS_TOKEN")
        ig_account_id = os.getenv("IG_BUSINESS_ACCOUNT_ID")

        if not access_token:
            return {"success": False, "error": "Missing Instagram access token — set IG_ACCESS_TOKEN in .env"}
        if not ig_account_id:
            return {"success": False, "error": "Missing Instagram Business Account ID — set IG_BUSINESS_ACCOUNT_ID in .env"}

        # --- Step 1: Generate image card from headline ---
        image_bytes = _generate_image_card(headlines)
        image_url = _upload_image_to_public_host(image_bytes)

        if not image_url:
            return {"success": False, "error": "Failed to host image"}

        # --- Step 2: Create media container ---
        container_url = f"{IG_GRAPH_URL}/{ig_account_id}/media"
        container_payload = {
            "image_url": image_url,
            "caption": caption,
            "access_token": access_token,
        }
        resp = requests.post(container_url, data=container_payload, timeout=30)
        resp.raise_for_status()
        creation_id = resp.json().get("id")

        if not creation_id:
            return {"success": False, "error": "Failed to create media container"}

        # --- Step 3: Wait for image processing, then publish ---
        time.sleep(5)
        publish_url = f"{IG_GRAPH_URL}/{ig_account_id}/media_publish"
        publish_payload = {
            "creation_id": creation_id,
            "access_token": access_token,
        }
        resp = requests.post(publish_url, data=publish_payload, timeout=30)
        resp.raise_for_status()
        media_id = resp.json().get("id", "")

        log.info("Posted to Instagram — media ID: %s", media_id)
        return {"success": True, "media_id": media_id}

    except Exception as e:
        log.error("Instagram post failed: %s", e)
        return {"success": False, "error": str(e)}


def _generate_image_card(headlines):
    """Generates a 1080x1080 image card with the headline text."""
    width, height = 1080, 1080
    bg_color = (20, 20, 30)
    text_color = (255, 255, 255)
    accent_color = (0, 150, 255)

    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Title
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        body_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
    except (IOError, OSError):
        title_font = ImageFont.load_default()
        body_font = ImageFont.load_default()

    # Header
    draw.text((50, 50), "BOBNews Daily", fill=accent_color, font=title_font)

    # Headlines
    y = 150
    for i, h in enumerate(headlines, 1):
        # Wrap text
        lines = _wrap_text(draw, f"{i}. {h['title']}", body_font, width - 100)
        for line in lines:
            draw.text((50, y), line, fill=text_color, font=body_font)
            y += 40
        y += 20

    # Footer
    draw.text((50, height - 60), "#BOBNews #DailyNews", fill=accent_color, font=body_font)

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


def _upload_image_to_public_host(image_bytes):
    """
    Upload image to a free public host so Instagram can fetch it.
    Primary: freeimage.host (free, no API key required)
    Fallback: 0x0.st
    Returns a direct image URL or None on failure.
    """
    import base64

    # Try freeimage.host first (reliable, returns direct image URL)
    try:
        image_bytes.seek(0)
        b64 = base64.b64encode(image_bytes.getvalue()).decode()
        resp = requests.post(
            "https://freeimage.host/api/1/upload",
            data={
                "key": "6d207e02198a847aa98d0a2a901485a5",  # public demo key
                "action": "upload",
                "source": b64,
                "type": "file",
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        if data.get("status_code") == 200 and data.get("image", {}).get("url"):
            url = data["image"]["url"]
            log.info("Image uploaded to freeimage.host: %s", url)
            return url
    except Exception as e:
        log.warning("freeimage.host upload failed: %s — trying fallback", e)

    # Fallback: 0x0.st
    try:
        image_bytes.seek(0)
        resp = requests.post(
            "https://0x0.st",
            files={"file": ("news.jpg", image_bytes, "image/jpeg")},
            timeout=30,
        )
        resp.raise_for_status()
        url = resp.text.strip()
        if url:
            log.info("Image uploaded to 0x0.st: %s", url)
            return url
    except Exception as e:
        log.error("0x0.st upload also failed: %s", e)

    return None

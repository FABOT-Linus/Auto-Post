"""Post to Instagram Business account via the Instagram Graph API.

Generates a professional news card image and posts it with a caption.
"""

import os
import io
import time
import logging
import requests
from image_generator import generate_news_image

log = logging.getLogger("instagram_poster")

IG_GRAPH_URL = "https://graph.facebook.com/v19.0"


def post_to_instagram(caption, headlines):
    """Generates an image card and posts to Instagram. Returns dict with success/status."""
    try:
        access_token = os.getenv("IG_ACCESS_TOKEN") or os.getenv("FACEBOOK_ACCESS_TOKEN")
        ig_account_id = os.getenv("IG_BUSINESS_ACCOUNT_ID")

        if not access_token:
            return {"success": False, "error": "Missing Instagram access token"}
        if not ig_account_id:
            return {"success": False, "error": "Missing Instagram Business Account ID"}

        # --- Step 1: Generate professional image card ---
        image_bytes = generate_news_image(headlines, platform="instagram")
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


def _upload_image_to_public_host(image_bytes):
    """Upload image to freeimage.host and return the direct URL."""
    import base64
    try:
        image_bytes.seek(0)
        b64 = base64.b64encode(image_bytes.getvalue()).decode()
        resp = requests.post(
            "https://freeimage.host/api/1/upload",
            data={
                "key": "6d207e02198a847aa98d0a2a901485a5",
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

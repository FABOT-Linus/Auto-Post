"""Post to Instagram Business account via the Instagram Graph API.

Supports two modes:
1. Carousel post (multiple slides) — when headlines are provided
2. Single image post — fallback
"""

import os
import io
import time
import logging
import requests
from image_generator import generate_news_image
from carousel_generator import generate_all_slides

log = logging.getLogger("instagram_poster")

IG_GRAPH_URL = "https://graph.facebook.com/v19.0"


def post_to_instagram(caption, headlines):
    """Posts a carousel of slides to Instagram. Returns dict with success/status."""
    try:
        access_token = os.getenv("IG_ACCESS_TOKEN") or os.getenv("FACEBOOK_ACCESS_TOKEN")
        ig_account_id = os.getenv("IG_BUSINESS_ACCOUNT_ID")

        if not access_token:
            return {"success": False, "error": "Missing Instagram access token"}
        if not ig_account_id:
            return {"success": False, "error": "Missing Instagram Business Account ID"}

        # --- Step 1: Generate all carousel slides ---
        log.info("Generating 5 carousel slides...")
        slides = generate_all_slides(headlines)

        # --- Step 2: Upload all slides to public host ---
        image_urls = []
        for i, slide in enumerate(slides, 1):
            url = _upload_image_to_public_host(slide)
            if url:
                image_urls.append(url)
                log.info("Slide %d uploaded: %s", i, url)
            else:
                log.warning("Slide %d upload failed", i)

        if not image_urls:
            return {"success": False, "error": "Failed to host any carousel images"}

        # --- Step 3: Create carousel (if 2+ images) or single post ---
        if len(image_urls) >= 2:
            log.info("Creating Instagram carousel with %d slides...", len(image_urls))

            # Create a children container for each image
            children_ids = []
            for i, img_url in enumerate(image_urls):
                resp = requests.post(
                    f"{IG_GRAPH_URL}/{ig_account_id}/media",
                    data={
                        "image_url": img_url,
                        "is_carousel_item": "true",
                        "access_token": access_token,
                    },
                    timeout=30,
                )
                resp.raise_for_status()
                child_id = resp.json().get("id")
                if child_id:
                    children_ids.append(child_id)
                    log.info("Carousel item %d created: %s", i + 1, child_id)

            if len(children_ids) < 2:
                log.warning("Not enough carousel items created, falling back to single image")
                # Fall back to single image
                resp = requests.post(
                    f"{IG_GRAPH_URL}/{ig_account_id}/media",
                    data={
                        "image_url": image_urls[0],
                        "caption": caption,
                        "access_token": access_token,
                    },
                    timeout=30,
                )
                resp.raise_for_status()
                creation_id = resp.json().get("id")
                time.sleep(5)
                resp = requests.post(
                    f"{IG_GRAPH_URL}/{ig_account_id}/media_publish",
                    data={"creation_id": creation_id, "access_token": access_token},
                    timeout=30,
                )
                resp.raise_for_status()
                media_id = resp.json().get("id", "")
                log.info("Posted single image to Instagram — media ID: %s", media_id)
                return {"success": True, "media_id": media_id, "carousel": False}

            # Create the carousel container
            children_param = ",".join(children_ids)
            resp = requests.post(
                f"{IG_GRAPH_URL}/{ig_account_id}/media",
                data={
                    "media_type": "CAROUSEL",
                    "children": children_param,
                    "caption": caption,
                    "access_token": access_token,
                },
                timeout=30,
            )
            resp.raise_for_status()
            creation_id = resp.json().get("id")

            if not creation_id:
                return {"success": False, "error": "Failed to create carousel container"}

            # Wait for processing then publish
            time.sleep(5)
            resp = requests.post(
                f"{IG_GRAPH_URL}/{ig_account_id}/media_publish",
                data={"creation_id": creation_id, "access_token": access_token},
                timeout=30,
            )
            resp.raise_for_status()
            media_id = resp.json().get("id", "")

            log.info("Posted carousel to Instagram — media ID: %s (%d slides)", media_id, len(children_ids))
            return {"success": True, "media_id": media_id, "carousel": True, "slides": len(children_ids)}

        else:
            # Single image fallback
            log.info("Posting single image to Instagram...")
            resp = requests.post(
                f"{IG_GRAPH_URL}/{ig_account_id}/media",
                data={
                    "image_url": image_urls[0],
                    "caption": caption,
                    "access_token": access_token,
                },
                timeout=30,
            )
            resp.raise_for_status()
            creation_id = resp.json().get("id")
            time.sleep(5)
            resp = requests.post(
                f"{IG_GRAPH_URL}/{ig_account_id}/media_publish",
                data={"creation_id": creation_id, "access_token": access_token},
                timeout=30,
            )
            resp.raise_for_status()
            media_id = resp.json().get("id", "")
            log.info("Posted single image to Instagram — media ID: %s", media_id)
            return {"success": True, "media_id": media_id, "carousel": False}

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
            return url
    except Exception as e:
        log.error("0x0.st upload also failed: %s", e)

    return None

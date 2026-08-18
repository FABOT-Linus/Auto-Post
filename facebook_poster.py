"""Post to a Facebook Page via the Graph API.

Posts an image (news card) with a text caption for maximum engagement.
Uploads image as binary data directly to Facebook (NOT via external hosting).
Falls back to text-only if image generation/upload fails.
"""

import os
import io
import logging
import requests
from image_generator import generate_news_image

log = logging.getLogger("facebook_poster")

FB_GRAPH_URL = "https://graph.facebook.com/v19.0"


def _get_access_token():
    """Resolve the Facebook page access token from either env var name."""
    return os.getenv("FB_PAGE_ACCESS_TOKEN") or os.getenv("FACEBOOK_ACCESS_TOKEN")


def _get_page_id():
    """Resolve the Facebook Page ID from either env var name."""
    return os.getenv("FB_PAGE_ID") or os.getenv("FACEBOOK_PAGE_ID")


def _resolve_page_token(access_token, page_id):
    """If the given token is a user token, fetch the page-specific access token."""
    try:
        resp = requests.get(
            f"{FB_GRAPH_URL}/me/accounts?access_token={access_token}",
            timeout=10,
        )
        if resp.status_code == 200:
            pages = resp.json().get("data", [])
            for page in pages:
                if page.get("id") == page_id:
                    page_token = page.get("access_token")
                    if page_token:
                        log.info("Extracted page access token for %s (%s)", page.get("name"), page_id)
                        return page_token
    except Exception as e:
        log.warning("Could not resolve page token: %s", e)
    return access_token


def post_to_facebook(text, headlines=None):
    """Posts an image card + caption to a Facebook Page.
    Uploads image as binary directly to Facebook API (no external hosting).
    Falls back to text-only if image upload fails.
    Returns dict with success/status."""
    try:
        access_token = _get_access_token()
        page_id = _get_page_id()

        if not access_token:
            return {"success": False, "error": "Missing Facebook access token"}
        if not page_id:
            return {"success": False, "error": "Missing Facebook Page ID"}

        # Resolve page token
        access_token = _resolve_page_token(access_token, page_id)

        # Try image post first (if headlines provided)
        if headlines:
            try:
                image_bytes = generate_news_image(headlines, platform="facebook")
                image_bytes.seek(0)

                log.info("Uploading image directly to Facebook (binary upload)...")
                # Upload image as binary multipart form data — NOT via external URL
                resp = requests.post(
                    f"{FB_GRAPH_URL}/{page_id}/photos",
                    data={
                        "message": text,
                        "access_token": access_token,
                    },
                    files={
                        "source": ("news_card.png", image_bytes, "image/png"),
                    },
                    timeout=60,
                )
                resp.raise_for_status()
                result = resp.json()
                post_id = result.get("post_id", result.get("id", ""))
                if post_id:
                    log.info("Posted to Facebook with image — post ID: %s", post_id)
                    return {"success": True, "post_id": post_id, "image": True}
            except Exception as e:
                log.warning("Image post failed, falling back to text: %s", e)

        # Fallback: text-only post
        log.info("Posting text-only to Facebook...")
        resp = requests.post(
            f"{FB_GRAPH_URL}/{page_id}/feed",
            data={"message": text, "access_token": access_token},
            timeout=30,
        )
        resp.raise_for_status()
        post_id = resp.json().get("id", "")
        log.info("Posted to Facebook (text only) — post ID: %s", post_id)
        return {"success": True, "post_id": post_id, "image": False}

    except Exception as e:
        log.error("Facebook post failed: %s", e)
        return {"success": False, "error": str(e)}

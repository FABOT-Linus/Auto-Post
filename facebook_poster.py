"""Post to a Facebook Page via the Graph API.

If the provided token is a user access token (not a page token), this module
automatically fetches the page-specific access token from /me/accounts.
"""

import os
import logging
import requests

log = logging.getLogger("facebook_poster")

FB_GRAPH_URL = "https://graph.facebook.com/v19.0"


def _get_access_token():
    """Resolve the Facebook page access token from either env var name."""
    return os.getenv("FB_PAGE_ACCESS_TOKEN") or os.getenv("FACEBOOK_ACCESS_TOKEN")


def _get_page_id():
    """Resolve the Facebook Page ID from either env var name."""
    return os.getenv("FB_PAGE_ID") or os.getenv("FACEBOOK_PAGE_ID")


def _resolve_page_token(access_token, page_id):
    """If the given token is a user token, fetch the page-specific access token.
    Returns the best token to use for posting as the page."""
    try:
        # Try fetching the page access token via /me/accounts
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
        # Token might already be a page token — return as-is
    except Exception as e:
        log.warning("Could not resolve page token: %s", e)

    return access_token


def post_to_facebook(text):
    """Posts a text update to a Facebook Page. Returns dict with success/status."""
    try:
        page_id = _get_page_id()
        access_token = _get_access_token()

        if not access_token:
            return {"success": False, "error": "Missing Facebook access token — set FB_PAGE_ACCESS_TOKEN or FACEBOOK_ACCESS_TOKEN in .env"}
        if not page_id:
            return {"success": False, "error": "Missing Facebook Page ID — set FB_PAGE_ID in .env"}

        # Resolve page-specific token (handles user tokens automatically)
        access_token = _resolve_page_token(access_token, page_id)

        url = f"{FB_GRAPH_URL}/{page_id}/feed"
        payload = {
            "message": text,
            "access_token": access_token,
        }

        resp = requests.post(url, data=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        post_id = data.get("id", "")
        log.info("Posted to Facebook — post ID: %s", post_id)
        return {"success": True, "post_id": post_id}

    except Exception as e:
        log.error("Facebook post failed: %s", e)
        return {"success": False, "error": str(e)}

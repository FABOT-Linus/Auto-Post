"""Post to LinkedIn via the LinkedIn API.

Posts a professional news card image with a text caption.
Falls back to text-only if image upload fails.
Uses the v2 UGC API which is compatible with the w_member_social scope.
"""

import os
import io
import json
import logging
import requests
from image_generator import generate_news_image

log = logging.getLogger("linkedin_poster")

LINKEDIN_API_URL = "https://api.linkedin.com/v2"


def post_to_linkedin(text, headlines=None):
    """Posts to LinkedIn — image card + caption if possible, text-only fallback.
    Returns dict with success/status."""
    try:
        access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
        member_urn = os.getenv("LINKEDIN_MEMBER_URN") or os.getenv("LINKEDIN_PERSON_ID")

        if not access_token:
            return {"success": False, "error": "Missing LinkedIn access token"}

        if member_urn:
            log.info("Using LinkedIn member URN: %s", member_urn)
        else:
            # Try to get the member URN from the API
            resp = requests.get(
                f"{LINKEDIN_API_URL}/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )
            if resp.status_code == 200:
                sub = resp.json().get("sub", "")
                if sub:
                    member_urn = f"urn:li:person:{sub}"
                    log.info("Retrieved LinkedIn member URN: %s", member_urn)

        if not member_urn:
            return {"success": False, "error": "Missing LinkedIn member URN — set LINKEDIN_MEMBER_URN"}

        author = member_urn

        # Common headers for v2 API
        headers = {
            "Authorization": f"Bearer {access_token}",
            "X-Restli-Protocol-Version": "2.0.0",
            "Content-Type": "application/json",
        }

        # Try image post first (if headlines provided)
        if headlines:
            try:
                image_url = _upload_image_to_public_host(headlines)
                if image_url:
                    log.info("Posting image card to LinkedIn...")

                    # Step 1: Register image upload via v2 assets API
                    register_resp = requests.post(
                        f"{LINKEDIN_API_URL}/assets?action=registerUpload",
                        headers=headers,
                        json={
                            "registerUploadRequest": {
                                "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                                "owner": author,
                            }
                        },
                        timeout=30,
                    )
                    register_resp.raise_for_status()
                    upload_data = register_resp.json().get("value", {})
                    upload_urn = upload_data.get("asset", "")
                    upload_url = upload_data.get("uploadMechanism", {}).get(
                        "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest", {}
                    ).get("uploadUrl", "")

                    if not upload_urn or not upload_url:
                        raise Exception("Failed to get LinkedIn image upload URL")

                    # Step 2: Download our image and upload to LinkedIn
                    img_resp = requests.get(image_url, timeout=30)
                    img_resp.raise_for_status()

                    upload_resp = requests.put(
                        upload_url,
                        headers={"Content-Type": "image/jpeg"},
                        data=img_resp.content,
                        timeout=60,
                    )
                    upload_resp.raise_for_status()

                    # Step 3: Create the UGC post with image
                    post_payload = {
                        "author": author,
                        "lifecycleState": "PUBLISHED",
                        "specificContent": {
                            "com.linkedin.ugc.ShareContent": {
                                "shareCommentary": {"value": text},
                                "shareMediaCategory": "IMAGE",
                                "media": [
                                    {
                                        "status": "READY",
                                        "description": {
                                            "text": "BOBNews Daily Market Digest"
                                        },
                                        "media": upload_urn,
                                        "title": {
                                            "text": "BOBNews Daily Market Digest"
                                        },
                                    }
                                ],
                            }
                        },
                        "visibility": {
                            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                        },
                    }

                    resp = requests.post(
                        f"{LINKEDIN_API_URL}/ugcPosts",
                        headers=headers,
                        json=post_payload,
                        timeout=30,
                    )
                    resp.raise_for_status()
                    post_urn = resp.json().get("id", "")
                    log.info("Posted to LinkedIn with image — post URN: %s", post_urn)
                    return {"success": True, "post_urn": post_urn, "image": True}

            except Exception as e:
                log.warning("LinkedIn image post failed, falling back to text: %s", e)

        # Fallback: Text-only post via v2 UGC API
        log.info("Posting text-only to LinkedIn as: %s", author)
        post_payload = {
            "author": author,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"value": text},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            },
        }

        resp = requests.post(
            f"{LINKEDIN_API_URL}/ugcPosts",
            headers=headers,
            json=post_payload,
            timeout=30,
        )
        resp.raise_for_status()
        post_urn = resp.json().get("id", "")
        log.info("Posted to LinkedIn (text only) — post URN: %s", post_urn)
        return {"success": True, "post_urn": post_urn, "image": False}

    except Exception as e:
        log.error("LinkedIn post failed: %s", e)
        return {"success": False, "error": str(e)}


def _upload_image_to_public_host(headlines):
    """Generate image and upload to freeimage.host."""
    import base64
    try:
        image_bytes = generate_news_image(headlines, platform="linkedin")
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
        log.warning("Image upload failed: %s", e)
    return None

"""Post to LinkedIn via the REST Posts API.

Supports both personal profile posts and company/organization page posts.

Auth modes:
1. Direct access token (LINKEDIN_ACCESS_TOKEN)
2. OAuth refresh using LINKEDIN_CLIENT_ID + LINKEDIN_CLIENT_SECRET + LINKEDIN_REFRESH_TOKEN

Author URN (priority order):
  1. LINKEDIN_ORG_URN  → posts as company page (urn:li:organization:XXXXX)
  2. LINKEDIN_MEMBER_URN → posts as personal profile (urn:li:person:XXXXX)
  3. Auto-fetch from /v2/userinfo (requires openid + profile scopes)

For company page posting, the token needs w_organization_social scope.
For personal posting, the token needs w_member_social scope.
"""

import os
import logging
import requests

log = logging.getLogger("linkedin_poster")

LINKEDIN_REST_POSTS_URL = "https://api.linkedin.com/rest/posts"
LINKEDIN_TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"

# REST API version — 202508 is the active version as of Aug 2026
LINKEDIN_API_VERSION = "202508"


def _refresh_access_token():
    """Exchange a refresh token for a new access token using client ID + secret.
    Returns the new access token, or None on failure."""
    client_id = os.getenv("LINKEDIN_CLIENT_ID")
    client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
    refresh_token = os.getenv("LINKEDIN_REFRESH_TOKEN")

    if not client_id or not client_secret or not refresh_token:
        return None

    try:
        resp = requests.post(
            LINKEDIN_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": refresh_token,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
        resp.raise_for_status()
        token = resp.json().get("access_token")
        if token:
            log.info("Successfully refreshed LinkedIn access token")
        return token
    except Exception as e:
        log.error("LinkedIn token refresh failed: %s", e)
        return None


def _get_access_token():
    """Resolve the access token — uses LINKEDIN_ACCESS_TOKEN directly, or
    refreshes via OAuth client credentials if only ID + secret + refresh token are set."""
    token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    if token and "your_" not in token:
        return token
    return _refresh_access_token()


def _get_author_urn(access_token):
    """Determine the author URN for posting.
    Priority:
      1. LINKEDIN_ORG_URN env var → company page (urn:li:organization:XXXXX)
      2. LINKEDIN_MEMBER_URN env var → personal profile (urn:li:person:XXXXX)
      3. Auto-fetch from /v2/userinfo (requires openid + profile scopes)
    Returns the URN string or None on failure."""
    # 1. Organization URN (company page) — highest priority
    org_urn = os.getenv("LINKEDIN_ORG_URN", "").strip()
    if org_urn and "your_" not in org_urn:
        log.info("Using LinkedIn organization URN: %s", org_urn)
        return org_urn

    # 2. Manually-set personal member URN
    member_urn = os.getenv("LINKEDIN_MEMBER_URN", "").strip()
    if member_urn and "your_" not in member_urn:
        log.info("Using LinkedIn member URN: %s", member_urn)
        return member_urn

    # 3. Auto-fetch from OIDC userinfo endpoint
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        resp = requests.get(LINKEDIN_USERINFO_URL, headers=headers, timeout=15)
        if resp.status_code == 200:
            sub = resp.json().get("sub")
            if sub:
                urn = f"urn:li:person:{sub}"
                log.info("Auto-fetched LinkedIn author URN: %s", urn)
                return urn
        else:
            log.warning("userinfo endpoint returned %d: %s", resp.status_code, resp.text[:200])
    except Exception as e:
        log.error("Failed to fetch LinkedIn userinfo: %s", e)

    log.warning(
        "Could not determine LinkedIn author URN. "
        "Set LINKEDIN_ORG_URN (company) or LINKEDIN_MEMBER_URN (personal) in .env, "
        "or ensure token has openid + profile scopes."
    )
    return None


def post_to_linkedin(text):
    """Posts a text update to LinkedIn (company page or personal profile via REST Posts API).
    Returns dict with success/status."""
    try:
        access_token = _get_access_token()
        if not access_token:
            return {
                "success": False,
                "error": "Missing LinkedIn credentials — need LINKEDIN_ACCESS_TOKEN or "
                "(LINKEDIN_CLIENT_ID + LINKEDIN_CLIENT_SECRET + LINKEDIN_REFRESH_TOKEN)",
            }

        author = _get_author_urn(access_token)
        if not author:
            return {
                "success": False,
                "error": (
                    "Could not determine LinkedIn author URN. Either:\n"
                    "  1. Set LINKEDIN_ORG_URN in .env (e.g. 'urn:li:organization:143071597'), or\n"
                    "  2. Set LINKEDIN_MEMBER_URN in .env (e.g. 'urn:li:person:dLBULrcoAR'), or\n"
                    "  3. Ensure token has openid + profile scopes so it can auto-fetch"
                ),
            }

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
            "LinkedIn-Version": LINKEDIN_API_VERSION,
        }

        payload = {
            "author": author,
            "commentary": text,
            "visibility": "PUBLIC",
            "distribution": {
                "feedDistribution": "MAIN_FEED",
                "targetEntities": [],
                "thirdPartyDistributionChannels": [],
            },
            "lifecycleState": "PUBLISHED",
            "isReshareDisabledByAuthor": False,
        }

        log.info("Posting to LinkedIn as: %s", author)
        resp = requests.post(LINKEDIN_REST_POSTS_URL, json=payload, headers=headers, timeout=15)

        if resp.status_code in (200, 201):
            post_id = resp.headers.get("x-restli-id", resp.headers.get("Location", ""))
            log.info("Posted to LinkedIn — ID: %s", post_id)
            return {"success": True, "post_id": post_id}

        # Error
        resp.raise_for_status()

    except Exception as e:
        log.error("LinkedIn post failed: %s", e)
        return {"success": False, "error": str(e)}

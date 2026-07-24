"""
social_poster.py
Functions that take generated content and publish it to each platform.
Each platform has different API requirements - see .env.example and the
README for how to obtain credentials.
"""

import os
import time
import requests


# ---------------------------------------------------------------------------
# LINKEDIN
# ---------------------------------------------------------------------------
def post_to_linkedin(text: str) -> dict:
    """
    Posts a text update to LinkedIn using the UGC Posts API.
    Requires LINKEDIN_ACCESS_TOKEN and LINKEDIN_PERSON_URN in the environment.
    """
    url = "https://api.linkedin.com/v2/ugcPosts"
    headers = {
        "Authorization": f"Bearer {os.environ['LINKEDIN_ACCESS_TOKEN']}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    payload = {
        "author": os.environ["LINKEDIN_PERSON_URN"],
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    return {"platform": "linkedin", "status": resp.status_code, "response": resp.json() if resp.text else {}}


# ---------------------------------------------------------------------------
# REDDIT
# ---------------------------------------------------------------------------
def post_to_reddit(title: str, body: str, first_comment: str = None) -> dict:
    """
    Posts a self (text) post to the configured subreddit, then optionally
    adds the expanded article summary as the first comment.
    Requires praw + Reddit script-app credentials.
    """
    import praw

    reddit = praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_CLIENT_SECRET"],
        username=os.environ["REDDIT_USERNAME"],
        password=os.environ["REDDIT_PASSWORD"],
        user_agent=os.environ["REDDIT_USER_AGENT"],
    )
    subreddit = reddit.subreddit(os.environ["REDDIT_SUBREDDIT"])
    submission = subreddit.submit(title=title, selftext=body)

    comment = None
    if first_comment:
        comment = submission.reply(first_comment)

    return {
        "platform": "reddit",
        "post_url": f"https://reddit.com{submission.permalink}",
        "comment_id": comment.id if comment else None,
    }


# ---------------------------------------------------------------------------
# INSTAGRAM (via Facebook Graph API - Instagram Business account)
# ---------------------------------------------------------------------------
def post_to_instagram(image_url: str, caption: str) -> dict:
    """
    Publishes an image post to Instagram.
    NOTE: Instagram's API requires the image to already be hosted at a
    public URL (image_url) - it does not accept raw file uploads. Generate
    the image first (see generate_image_from_prompt below) and host it
    somewhere public (e.g. S3, Cloudinary, or your own server) before
    calling this function.

    Requires IG_ACCESS_TOKEN and IG_BUSINESS_ACCOUNT_ID.
    """
    ig_user_id = os.environ["IG_BUSINESS_ACCOUNT_ID"]
    access_token = os.environ["IG_ACCESS_TOKEN"]
    base_url = f"https://graph.facebook.com/v19.0/{ig_user_id}"

    # Step 1: create a media container
    container_resp = requests.post(
        f"{base_url}/media",
        data={"image_url": image_url, "caption": caption, "access_token": access_token},
        timeout=30,
    )
    container_resp.raise_for_status()
    creation_id = container_resp.json()["id"]

    # Step 2: poll until the container has finished processing
    status_url = f"https://graph.facebook.com/v19.0/{creation_id}"
    for _ in range(10):
        status_resp = requests.get(
            status_url, params={"fields": "status_code", "access_token": access_token}, timeout=30
        )
        status_resp.raise_for_status()
        if status_resp.json().get("status_code") == "FINISHED":
            break
        time.sleep(3)

    # Step 3: publish the container
    publish_resp = requests.post(
        f"{base_url}/media_publish",
        data={"creation_id": creation_id, "access_token": access_token},
        timeout=30,
    )
    publish_resp.raise_for_status()
    return {"platform": "instagram", "response": publish_resp.json()}


# ---------------------------------------------------------------------------
# Generate the Instagram image with Pollinations.ai (free, no API key)
# ---------------------------------------------------------------------------
def generate_image_from_prompt(prompt: str, out_path: str = "instagram_image.png",
                                width: int = 1024, height: int = 1024, seed: int = None) -> dict:
    """
    Generates an image from the Instagram image prompt using Pollinations.ai
    (https://pollinations.ai) - completely free, no API key required.

    Returns a dict with:
      - "url": a publicly accessible image URL you can pass DIRECTLY to
        post_to_instagram() - no separate hosting/upload step needed.
      - "local_path": a local copy of the same image, saved for your own
        review before posting.

    Swap this out for Midjourney/Flux/Stable Diffusion if you prefer -
    just make sure whatever you swap in also returns a public URL.
    """
    from urllib.parse import quote
    import random

    if seed is None:
        seed = random.randint(0, 2**31 - 1)  # avoids Pollinations' response cache reusing an old image

    encoded_prompt = quote(prompt)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?width={width}&height={height}&seed={seed}&nologo=true"
    )

    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(resp.content)

    return {"url": url, "local_path": out_path}

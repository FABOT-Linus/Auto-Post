"""Daily Financial News Social Media Poster — main entry point."""

import os
import sys
import logging
from dotenv import load_dotenv

from news_fetcher import fetch_top_headlines
from formatter import format_posts

load_dotenv(override=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("daily-news-poster")


def _getenv(key, default):
    """Get env var, returning default if missing or empty string."""
    val = os.getenv(key, "").strip()
    return val if val else default


def main():
    log.info("=== Daily Financial News Social Media Poster ===")

    # --- Fetch financial news ---
    keywords = _getenv("NEWS_KEYWORDS", "stock market,economy,investing")
    categories = _getenv("NEWS_CATEGORIES", "business")
    try:
        max_headlines = int(_getenv("MAX_HEADLINES", "3"))
    except ValueError:
        max_headlines = 3

    try:
        headlines = fetch_top_headlines(
            api_key=os.getenv("NEWS_API_KEY"),
            keywords=keywords,
            categories=categories,
            max_results=max_headlines,
        )
    except Exception as e:
        log.error("News fetch failed completely: %s", e)
        headlines = []

    if not headlines:
        log.warning("No headlines fetched — exiting.")
        return

    log.info("Fetched %d financial headlines:", len(headlines))
    for h in headlines:
        log.info("  • %s — %s", h["title"], h["source"])

    # --- Format for each platform ---
    posts = format_posts(headlines)

    # --- Post to enabled platforms ---
    results = {}

    if _getenv("ENABLE_X", "false").lower() == "true":
        try:
            from x_poster import post_to_x
            log.info("Posting to X.com...")
            results["x"] = post_to_x(posts["x"], headlines=headlines)
            log.info("X.com result: %s", results["x"])
        except Exception as e:
            log.error("X.com post failed: %s", e)
            results["x"] = {"success": False, "error": str(e)}

    if _getenv("ENABLE_FACEBOOK", "false").lower() == "true":
        try:
            from facebook_poster import post_to_facebook
            log.info("Posting to Facebook...")
            results["facebook"] = post_to_facebook(posts["facebook"])
            log.info("Facebook result: %s", results["facebook"])
        except Exception as e:
            log.error("Facebook post failed: %s", e)
            results["facebook"] = {"success": False, "error": str(e)}

    if _getenv("ENABLE_INSTAGRAM", "false").lower() == "true":
        try:
            from instagram_poster import post_to_instagram
            log.info("Posting to Instagram...")
            results["instagram"] = post_to_instagram(posts["instagram"], headlines)
            log.info("Instagram result: %s", results["instagram"])
        except Exception as e:
            log.error("Instagram post failed: %s", e)
            results["instagram"] = {"success": False, "error": str(e)}

    if _getenv("ENABLE_LINKEDIN", "false").lower() == "true":
        try:
            from linkedin_poster import post_to_linkedin
            log.info("Posting to LinkedIn...")
            results["linkedin"] = post_to_linkedin(posts["linkedin"])
            log.info("LinkedIn result: %s", results["linkedin"])
        except Exception as e:
            log.error("LinkedIn post failed: %s", e)
            results["linkedin"] = {"success": False, "error": str(e)}

    log.info("=== Done! Summary: %s ===", results)


if __name__ == "__main__":
    main()

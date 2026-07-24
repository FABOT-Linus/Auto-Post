"""
main.py
Orchestrates the full pipeline:
  1. Read today's newsletter email (or fetch Google News top stories)
  2. Generate platform-specific content with Groq's free-tier LLM API
  3. Post to LinkedIn, Reddit, and (optionally) Instagram

Run once:
    python main.py

Run as a daily scheduled job (e.g. every morning at 8:00 AM):
    python main.py --schedule

You can also just run this file via cron / Task Scheduler instead of using
the built-in --schedule mode.
"""

import argparse
import traceback
from dotenv import load_dotenv

from email_reader import fetch_todays_newsletter
from google_news_fetcher import fetch_top_stories, format_as_digest
from content_generator import generate_social_content, parse_content
from social_poster import post_to_linkedin, post_to_reddit, post_to_instagram, generate_image_from_prompt

load_dotenv()


def get_source_content(source: str, top_n: int = 5, topic: str = None, query: str = None):
    """
    Returns (label, article_text) from the chosen source, or (None, None)
    if nothing was found.
    """
    if source == "google-news":
        print(f"[1/4] Fetching top {top_n} stories from Google News RSS...")
        stories = fetch_top_stories(n=top_n, topic=topic, query=query)
        if not stories:
            return None, None
        for s in stories:
            print(f"  - {s['title']} ({s['source']})")
        return "Google News top stories", format_as_digest(stories)

    # default: email newsletter
    print("[1/4] Checking email for today's newsletter...")
    email_data = fetch_todays_newsletter()
    if not email_data:
        return None, None
    print(f"  Found email: {email_data['subject']}")
    return email_data["subject"], email_data["body"]


def run_pipeline(dry_run: bool = False, do_instagram: bool = False, source: str = "email",
                  top_n: int = 5, topic: str = None, query: str = None):
    label, article_text = get_source_content(source, top_n=top_n, topic=topic, query=query)
    if not article_text:
        print("No content found for today. Exiting.")
        return

    print("[2/4] Generating platform-specific content with Groq...")
    raw = generate_social_content(article_text)
    content = parse_content(raw)

    print("\n----- GENERATED CONTENT -----")
    for key, value in content.items():
        print(f"\n--- {key} ---\n{value}")
    print("\n------------------------------\n")

    if dry_run:
        print("Dry run enabled - skipping actual posting.")
        return

    print("[3/4] Posting to LinkedIn and Reddit...")
    results = []
    try:
        results.append(post_to_linkedin(content["linkedin"]))
        print("  LinkedIn: posted.")
    except Exception:
        print("  LinkedIn: FAILED")
        traceback.print_exc()

    try:
        results.append(
            post_to_reddit(
                content["reddit_title"],
                content["reddit_post"],
                content["reddit_comment"],
            )
        )
        print("  Reddit: posted.")
    except Exception:
        print("  Reddit: FAILED")
        traceback.print_exc()

    if do_instagram:
        print("[4/4] Generating + posting Instagram image (via Pollinations.ai)...")
        try:
            image = generate_image_from_prompt(content["instagram_image_prompt"])
            print(f"  Image generated: {image['url']}")
            print(f"  Local copy saved at {image['local_path']} for your review.")
            results.append(post_to_instagram(image["url"], content["instagram_caption"]))
            print("  Instagram: posted.")
        except Exception:
            print("  Instagram: FAILED")
            traceback.print_exc()
    else:
        print("[4/4] Skipping Instagram (pass --instagram to enable).")

    print("\nDone. Results:")
    for r in results:
        print(" ", r)


def run_scheduler(source: str = "email", top_n: int = 5, topic: str = None, query: str = None):
    from apscheduler.schedulers.blocking import BlockingScheduler

    scheduler = BlockingScheduler()
    # Runs every day at 8:00 AM local time - adjust as needed
    scheduler.add_job(
        run_pipeline, "cron", hour=8, minute=0,
        kwargs={"source": source, "top_n": top_n, "topic": topic, "query": query},
    )
    print("Scheduler started. Waiting for the next scheduled run (daily 8:00 AM)...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Newsletter -> Social Media automation")
    parser.add_argument("--dry-run", action="store_true", help="Generate content but don't post it")
    parser.add_argument("--instagram", action="store_true", help="Also attempt Instagram image generation")
    parser.add_argument("--schedule", action="store_true", help="Run continuously on a daily schedule")
    parser.add_argument(
        "--source", choices=["email", "google-news"], default="email",
        help="Where to pull content from: your newsletter email (default) or Google News RSS",
    )
    parser.add_argument("--top-n", type=int, default=5, help="Number of Google News stories to pull (default 5)")
    parser.add_argument(
        "--topic", default=None,
        help="Optional Google News topic section, e.g. BUSINESS, TECHNOLOGY, WORLD, SPORTS, SCIENCE, HEALTH",
    )
    parser.add_argument("--query", default=None, help="Optional Google News keyword search instead of top stories")
    args = parser.parse_args()

    if args.schedule:
        run_scheduler(source=args.source, top_n=args.top_n, topic=args.topic, query=args.query)
    else:
        run_pipeline(
            dry_run=args.dry_run,
            do_instagram=args.instagram,
            source=args.source,
            top_n=args.top_n,
            topic=args.topic,
            query=args.query,
        )

"""Quick test to check if posting functions are even being called."""

import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("quick_test")

def main():
    log.info("=== Quick Platform Check ===")
    
    # Check enable flags
    log.info(f"ENABLE_FACEBOOK: {os.getenv('ENABLE_FACEBOOK', 'false')}")
    log.info(f"ENABLE_INSTAGRAM: {os.getenv('ENABLE_INSTAGRAM', 'false')}")
    log.info(f"ENABLE_LINKEDIN: {os.getenv('ENABLE_LINKEDIN', 'false')}")
    
    # Check credentials presence
    log.info(f"FB_PAGE_ACCESS_TOKEN present: {bool(os.getenv('FB_PAGE_ACCESS_TOKEN') or os.getenv('FACEBOOK_ACCESS_TOKEN'))}")
    log.info(f"FB_PAGE_ID present: {bool(os.getenv('FB_PAGE_ID') or os.getenv('FACEBOOK_PAGE_ID'))}")
    log.info(f"IG_ACCESS_TOKEN present: {bool(os.getenv('IG_ACCESS_TOKEN') or os.getenv('FACEBOOK_ACCESS_TOKEN'))}")
    log.info(f"IG_BUSINESS_ACCOUNT_ID present: {bool(os.getenv('IG_BUSINESS_ACCOUNT_ID'))}")
    log.info(f"LINKEDIN_ACCESS_TOKEN present: {bool(os.getenv('LINKEDIN_ACCESS_TOKEN'))}")
    log.info(f"LINKEDIN_MEMBER_URN present: {bool(os.getenv('LINKEDIN_MEMBER_URN') or os.getenv('LINKEDIN_PERSON_ID'))}")
    log.info(f"IMGBB_API_KEY present: {bool(os.getenv('IMGBB_API_KEY'))}")
    
    # Try to run a minimal version of main.py
    log.info("\n=== Running minimal main.py logic ===")
    
    try:
        from news_fetcher import fetch_top_headlines
        from formatter import format_posts
        
        keywords = os.getenv("NEWS_KEYWORDS", "stock market,economy,investing")
        categories = os.getenv("NEWS_CATEGORIES", "business")
        max_headlines = int(os.getenv("MAX_HEADLINES", "3"))
        
        log.info(f"Fetching headlines with keywords: {keywords}")
        headlines = fetch_top_headlines(
            api_key=os.getenv("NEWS_API_KEY"),
            keywords=keywords,
            categories=categories,
            max_results=max_headlines,
        )
        
        if not headlines:
            log.warning("No headlines fetched - this could be the issue!")
            return
        
        log.info(f"Fetched {len(headlines)} headlines")
        posts = format_posts(headlines)
        
        # Test each platform posting function
        if os.getenv("ENABLE_FACEBOOK", "false").lower() == "true":
            log.info("=== Testing Facebook ===")
            try:
                from facebook_poster import post_to_facebook
                result = post_to_facebook(posts["facebook"], headlines=headlines)
                log.info(f"Facebook result: {result}")
            except Exception as e:
                log.error(f"Facebook error: {e}")
                import traceback
                log.error(traceback.format_exc())
        
        if os.getenv("ENABLE_INSTAGRAM", "false").lower() == "true":
            log.info("=== Testing Instagram ===")
            try:
                from instagram_poster import post_to_instagram
                result = post_to_instagram(posts["instagram"], headlines)
                log.info(f"Instagram result: {result}")
            except Exception as e:
                log.error(f"Instagram error: {e}")
                import traceback
                log.error(traceback.format_exc())
        
        if os.getenv("ENABLE_LINKEDIN", "false").lower() == "true":
            log.info("=== Testing LinkedIn ===")
            try:
                from linkedin_poster import post_to_linkedin
                result = post_to_linkedin(posts["linkedin"], headlines=headlines)
                log.info(f"LinkedIn result: {result}")
            except Exception as e:
                log.error(f"LinkedIn error: {e}")
                import traceback
                log.error(traceback.format_exc())
                
    except Exception as e:
        log.error(f"Main logic error: {e}")
        import traceback
        log.error(traceback.format_exc())

if __name__ == "__main__":
    main()
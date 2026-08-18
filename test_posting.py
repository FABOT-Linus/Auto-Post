"""Test script to debug posting issues for Facebook, Instagram, and LinkedIn."""

import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
log = logging.getLogger("test_posting")

def test_facebook():
    """Test Facebook posting with detailed error reporting."""
    log.info("=== Testing Facebook Posting ===")
    
    access_token = os.getenv("FB_PAGE_ACCESS_TOKEN") or os.getenv("FACEBOOK_ACCESS_TOKEN")
    page_id = os.getenv("FB_PAGE_ID") or os.getenv("FACEBOOK_PAGE_ID")
    
    log.info(f"Access Token present: {bool(access_token)}")
    log.info(f"Page ID present: {bool(page_id)}")
    log.info(f"Page ID: {page_id}")
    
    if not access_token:
        log.error("❌ Missing Facebook access token")
        return False
    if not page_id:
        log.error("❌ Missing Facebook Page ID")
        return False
    
    try:
        from facebook_poster import post_to_facebook
        test_text = "📊 Test post from BOBNews - testing Facebook integration"
        test_headlines = [
            {"title": "Test Headline for Facebook", "source": "Test Source", "url": "https://example.com"}
        ]
        
        result = post_to_facebook(test_text, headlines=test_headlines)
        log.info(f"Facebook result: {result}")
        
        if result.get("success"):
            log.info("✅ Facebook test successful")
            return True
        else:
            log.error(f"❌ Facebook test failed: {result.get('error')}")
            return False
    except Exception as e:
        log.error(f"❌ Facebook test exception: {e}")
        import traceback
        log.error(traceback.format_exc())
        return False

def test_instagram():
    """Test Instagram posting with detailed error reporting."""
    log.info("=== Testing Instagram Posting ===")
    
    access_token = os.getenv("IG_ACCESS_TOKEN") or os.getenv("FACEBOOK_ACCESS_TOKEN")
    ig_account_id = os.getenv("IG_BUSINESS_ACCOUNT_ID")
    
    log.info(f"Access Token present: {bool(access_token)}")
    log.info(f"IG Business Account ID present: {bool(ig_account_id)}")
    log.info(f"IG Business Account ID: {ig_account_id}")
    
    if not access_token:
        log.error("❌ Missing Instagram access token")
        return False
    if not ig_account_id:
        log.error("❌ Missing Instagram Business Account ID")
        return False
    
    try:
        from instagram_poster import post_to_instagram
        test_caption = "📊 Test post from BOBNews - testing Instagram integration"
        test_headlines = [
            {"title": "Test Headline for Instagram", "source": "Test Source", "url": "https://example.com"}
        ]
        
        result = post_to_instagram(test_caption, test_headlines)
        log.info(f"Instagram result: {result}")
        
        if result.get("success"):
            log.info("✅ Instagram test successful")
            return True
        else:
            log.error(f"❌ Instagram test failed: {result.get('error')}")
            return False
    except Exception as e:
        log.error(f"❌ Instagram test exception: {e}")
        import traceback
        log.error(traceback.format_exc())
        return False

def test_linkedin():
    """Test LinkedIn posting with detailed error reporting."""
    log.info("=== Testing LinkedIn Posting ===")
    
    access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    member_urn = os.getenv("LINKEDIN_MEMBER_URN") or os.getenv("LINKEDIN_PERSON_ID")
    
    log.info(f"Access Token present: {bool(access_token)}")
    log.info(f"Member URN present: {bool(member_urn)}")
    log.info(f"Member URN: {member_urn}")
    
    if not access_token:
        log.error("❌ Missing LinkedIn access token")
        return False
    if not member_urn:
        log.error("❌ Missing LinkedIn member URN")
        return False
    
    try:
        from linkedin_poster import post_to_linkedin
        test_text = "📊 Test post from BOBNews - testing LinkedIn integration"
        test_headlines = [
            {"title": "Test Headline for LinkedIn", "source": "Test Source", "url": "https://example.com"}
        ]
        
        result = post_to_linkedin(test_text, headlines=test_headlines)
        log.info(f"LinkedIn result: {result}")
        
        if result.get("success"):
            log.info("✅ LinkedIn test successful")
            return True
        else:
            log.error(f"❌ LinkedIn test failed: {result.get('error')}")
            return False
    except Exception as e:
        log.error(f"❌ LinkedIn test exception: {e}")
        import traceback
        log.error(traceback.format_exc())
        return False

def main():
    log.info("Starting platform posting tests...")
    
    # Test each platform
    results = {
        "facebook": test_facebook(),
        "instagram": test_instagram(),
        "linkedin": test_linkedin(),
    }
    
    log.info("\n=== Test Summary ===")
    for platform, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        log.info(f"{platform.upper()}: {status}")
    
    overall_success = all(results.values())
    if overall_success:
        log.info("\n🎉 All platforms passed!")
    else:
        log.info("\n⚠️ Some platforms failed - check logs above for details")

if __name__ == "__main__":
    main()
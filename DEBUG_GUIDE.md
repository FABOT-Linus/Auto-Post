# Debugging Guide for Social Media Posting Issues

## Quick Test

Run the quick test to see what's happening:

```bash
cd 97c58952d_Auto-Post-FIXED
python quick_test.py
```

This will show you:
- Which platforms are enabled
- Which credentials are present/missing
- Whether headlines are being fetched
- The actual API responses from each platform

## Common Issues and Solutions

### 1. No Posts Appearing - But No Errors

**Cause**: The script might be completing successfully but posts aren't visible due to:
- Wrong Page ID / Account ID
- Insufficient API permissions
- Posts going to wrong page/account
- Privacy settings on posts

**Solution**: 
- Check the GitHub Actions logs for the actual post IDs returned
- Manually visit those post URLs to see if they exist
- Verify your Page IDs and Account IDs are correct
- Check that your API tokens have the right permissions

### 2. Image Upload Failures

**Cause**: Image hosting services might be failing

**Solution**:
- Check logs for "Image uploaded to..." messages
- If all image hosting fails, the script should fall back to text-only posts
- Add IMGBB_API_KEY to GitHub Secrets for better reliability

### 3. API Token Issues

**Cause**: Access tokens might be expired or have wrong permissions

**Solution**:
- Regenerate your access tokens
- For Facebook: Make sure token has `pages_manage_posts` permission
- For Instagram: Make sure token has `instagram_basic` and `pages_manage_posts` permissions
- For LinkedIn: Make sure token has `w_member_social` permission

### 4. Wrong Page/Account IDs

**Cause**: Using personal profile IDs instead of Page/Business Account IDs

**Solution**:
- Facebook: Must use a Page ID, not personal profile ID
- Instagram: Must use Business Account ID from Facebook Business Suite
- LinkedIn: Can use personal URN or organization URN

## What to Check in GitHub Actions Logs

Look for these specific log messages:

### Facebook
- "Facebook access token: Present/MISSING"
- "Facebook page ID: [ID or MISSING]"
- "Page token resolved: Success/Failed"
- "Image uploaded to..." or "Image post failed, falling back to text"
- "Facebook API response status: [HTTP code]"
- "Posted to Facebook — post ID: [ID]"

### Instagram
- "Instagram access token: Present/MISSING"
- "Instagram business account ID: [ID or MISSING]"
- "Image uploaded to..." or "upload failed"
- "Instagram carousel item API response status: [HTTP code]"
- "Posted carousel to Instagram — media ID: [ID]"

### LinkedIn
- "LinkedIn access token: Present/MISSING"
- "LinkedIn member URN: [URN or MISSING]"
- "Image uploaded to..." or "Image upload failed"
- "LinkedIn asset registration status: [HTTP code]"
- "LinkedIn UGC post status: [HTTP code]"
- "Posted to LinkedIn — post URN: [URN]"

## Manual Testing

Test each platform individually:

```bash
# Test only Facebook
ENABLE_FACEBOOK=true python test_posting.py

# Test only Instagram  
ENABLE_INSTAGRAM=true python test_posting.py

# Test only LinkedIn
ENABLE_LINKEDIN=true python test_posting.py
```

## Getting Help

If you're still seeing issues:

1. Run `python quick_test.py` and share the output
2. Check the GitHub Actions logs for the specific error messages
3. Verify your API credentials are correct and not expired
4. Make sure your Page IDs and Account IDs are for the right accounts

The most common issue is using the wrong Page/Account IDs or having expired API tokens.
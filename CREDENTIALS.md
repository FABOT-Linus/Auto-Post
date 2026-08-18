# Credentials Guide

This guide walks you through obtaining every API key and token needed for the Daily News Social Media Poster.

---

## 1. NewsAPI (News Headlines)

**Where**: https://newsapi.org/

1. Sign up for a free account
2. Go to your dashboard → grab your **API Key**
3. Free tier: 100 requests/day, 15-day article delay
4. Developer tier ($449/mo): no delay, 1000 req/day

**Credentials:**
```
NEWS_API_KEY=your_api_key_here
```

**Alternative (free, no key):** The script also supports RSS feeds as a fallback — see `src/news_fetcher.py`. No key needed.

---

## 2. X.com (Twitter)

**Where**: https://developer.x.com/

1. Sign up for a developer account
2. Create a new **Project & App**
3. Go to **Keys and Tokens** tab
4. Set user authentication settings to **Read and Write**
5. Generate the following:

**Credentials:**
```
X_API_KEY=your_x_api_key
X_API_SECRET=your_x_api_secret
X_ACCESS_TOKEN=your_x_access_token
X_ACCESS_TOKEN_SECRET=your_x_access_token_secret
```

**Notes:**
- Free tier allows 1,500 posts/month
- Access tokens are user-specific (posts as your account)
- For a bot account, create a separate X account and generate keys for that account

---

## 3. Facebook (Page Posting)

**Where**: https://developers.facebook.com/

1. Create a new **App** at developers.facebook.com
2. Add the **Facebook Login** product
3. Add **Pages** permissions: `pages_manage_posts`, `pages_read_engagement`
4. Get your **App ID** and **App Secret** from Settings → Basic
5. Generate a **Page Access Token**:
   - Use the Graph API Explorer: https://developers.facebook.com/tools/explorer/
   - Select your Page
   - Add permissions: `pages_manage_posts`, `pages_read_engagement`
   - Generate token (this is a short-lived token — exchange for long-lived, see below)
6. Get your **Page ID** from your Facebook Page → About → Page ID

**Long-lived token exchange:**
```
GET https://graph.facebook.com/v19.0/oauth/access_token
  ?grant_type=fb_exchange_token
  &client_id={APP_ID}
  &client_secret={APP_SECRET}
  &fb_exchange_token={SHORT_LIVED_TOKEN}
```

**Credentials:**
```
FB_APP_ID=your_app_id
FB_APP_SECRET=your_app_secret
FB_PAGE_ACCESS_TOKEN=your_long_lived_page_token
FB_PAGE_ID=your_page_id
```

**Notes:**
- You must be an admin of the Facebook Page
- Long-lived tokens expire in ~60 days — set a reminder to refresh
- Facebook posts from personal profiles are NOT supported via API

---

## 4. Instagram (Business Account)

**Where**: Instagram Graph API (through Facebook)

1. Your Instagram account must be a **Business or Creator** account
2. Link your Instagram to a **Facebook Page** (Instagram → Settings → Business/Creator → Linked Facebook Page)
3. Use the same Facebook App from step 3
4. Add **Instagram Graph API** permissions: `instagram_basic`, `instagram_content_publish`
5. Get your **Instagram Business Account ID**:
   - Graph API Explorer: `GET /me/accounts` → find your page → `instagram_business_account` field
6. Generate a long-lived access token (same process as Facebook, with Instagram permissions)

**Credentials:**
```
IG_ACCESS_TOKEN=your_instagram_access_token
IG_BUSINESS_ACCOUNT_ID=your_ig_business_account_id
```

**Important:**
- Instagram **cannot post text-only** — the script generates an image card from the headline
- The image is uploaded as a two-step process: create media container, then publish
- You need a background image or the script generates one (see `src/posters/instagram_poster.py`)

---

## 5. LinkedIn

**Where**: https://www.linkedin.com/developers/

1. Go to https://www.linkedin.com/developers/ and create a new **App**
2. Add the **Share on LinkedIn** and/or **Marketing Developer Platform** product
3. Get your **Client ID** and **Client Secret** from the App settings
4. Generate an **Access Token** and **Refresh Token** via OAuth2:
   - Auth URL: `https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=openid%20profile%20w_member_social`
   - Visit the auth URL in a browser, authorize the app, and get the `code` from the redirect
   - Exchange the code for tokens:
     ```
     POST https://www.linkedin.com/oauth/v2/accessToken
     grant_type=authorization_code
     code={AUTH_CODE}
     client_id={CLIENT_ID}
     client_secret={CLIENT_SECRET}
     redirect_uri={REDIRECT_URI}
     ```
   - The response contains `access_token` and `refresh_token`
   - Scopes: `w_member_social` (for personal posts) or `organization_social_actions` (for org)
5. Get your **Person ID** (URN):
   - `GET https://api.linkedin.com/v2/userinfo` with Bearer token
   - The `sub` field is your person ID
   - If not set, the script will auto-fetch it from the token

**Credentials:**
```
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_ACCESS_TOKEN=your_access_token
LINKEDIN_REFRESH_TOKEN=your_refresh_token
LINKEDIN_PERSON_ID=urn:li:person:ABC123  # optional — auto-fetched if missing
```

**For organization posts**, use:
```
LINKEDIN_ORG_URN=urn:li:organization:12345
```

**Auth modes (the script supports both):**
- **Direct token**: Set `LINKEDIN_ACCESS_TOKEN` — the script uses it as-is
- **Auto-refresh**: Set `LINKEDIN_CLIENT_ID` + `LINKEDIN_CLIENT_SECRET` + `LINKEDIN_REFRESH_TOKEN` — the script automatically refreshes the access token before posting

**Notes:**
- LinkedIn access tokens expire in 60 days — the refresh token lets the script auto-renew
- For org posting, you must be an admin of the LinkedIn Page
- You must complete the 3-legged OAuth flow at least once to obtain the initial access + refresh tokens

---

## Summary: All Environment Variables

Create a `.env` file (or GitHub Secrets) with:

```env
# News
NEWS_API_KEY=your_newsapi_key

# X.com (Twitter)
X_API_KEY=your_x_api_key
X_API_SECRET=your_x_api_secret
X_ACCESS_TOKEN=your_x_access_token
X_ACCESS_TOKEN_SECRET=your_x_access_token_secret

# Facebook
FB_APP_ID=your_fb_app_id
FB_APP_SECRET=your_fb_app_secret
FB_PAGE_ACCESS_TOKEN=your_fb_page_access_token
FB_PAGE_ID=your_fb_page_id

# Instagram
IG_ACCESS_TOKEN=your_ig_access_token
IG_BUSINESS_ACCOUNT_ID=your_ig_business_account_id

# LinkedIn
LINKEDIN_CLIENT_ID=your_linkedin_client_id
LINKEDIN_CLIENT_SECRET=your_linkedin_client_secret
LINKEDIN_ACCESS_TOKEN=your_linkedin_access_token
LINKEDIN_REFRESH_TOKEN=your_linkedin_refresh_token
LINKEDIN_PERSON_ID=urn:li:person:your_person_id

# Optional settings
NEWS_KEYWORDS=technology,AI,startup
NEWS_CATEGORIES=technology,science
MAX_HEADLINES=3
ENABLE_X=true
ENABLE_FACEBOOK=true
ENABLE_INSTAGRAM=true
ENABLE_LINKEDIN=true
```

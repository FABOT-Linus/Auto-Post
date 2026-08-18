# Setup Checklist — Come Back Here When You Have Your Credentials

Once you've collected your API keys, paste them to Alfred and he'll help you fill in the code.
Here's exactly what you need for each platform:

## ✅ NewsAPI (done)
- [x] NEWS_API_KEY

## 🐦 X.com (Twitter)
- [ ] X_API_KEY
- [ ] X_API_SECRET
- [ ] X_ACCESS_TOKEN
- [ ] X_ACCESS_TOKEN_SECRET
- [ ] ENABLE_X_IMAGE (true/false — whether to attach an image card to tweets)

## 📘 Facebook
- [ ] FB_APP_ID
- [ ] FB_APP_SECRET
- [ ] FB_PAGE_ACCESS_TOKEN (long-lived)
- [ ] FB_PAGE_ID

## 📸 Instagram
- [ ] IG_ACCESS_TOKEN
- [ ] IG_BUSINESS_ACCOUNT_ID

## 💼 LinkedIn
- [x] LINKEDIN_CLIENT_ID
- [x] LINKEDIN_CLIENT_SECRET
- [ ] LINKEDIN_ACCESS_TOKEN (obtained via OAuth — see CREDENTIALS.md)
- [ ] LINKEDIN_REFRESH_TOKEN (obtained via OAuth — see CREDENTIALS.md)
- [ ] LINKEDIN_PERSON_ID (format: urn:li:person:XXXXXX)

## ⚙️ Optional Settings
- [ ] NEWS_KEYWORDS (default: "stock market,economy,investing")
- [ ] MAX_HEADLINES (default: 3)
- [ ] ENABLE_X (true/false)
- [ ] ENABLE_FACEBOOK (true/false)
- [ ] ENABLE_INSTAGRAM (true/false)
- [ ] ENABLE_LINKEDIN (true/false)

---

## How to Run

### Local testing:
```bash
cp .env.example .env
# Fill in .env with your credentials
pip install -r requirements.txt
cd src
python main.py
```

### GitHub Actions (daily automation):
1. Push this repo to GitHub (make it public for free Actions)
2. Go to Settings → Secrets and variables → Actions
3. Add each credential as a repository secret
4. Go to Actions tab → "Daily Financial News Post" → Run workflow to test
5. It will run automatically at 08:00 UTC daily

### Toggle platforms on/off:
- In GitHub: Settings → Secrets and variables → Variables (not Secrets)
- Add variables like ENABLE_X=true, ENABLE_FACEBOOK=false, etc.
- Or just don't add the secrets for a platform — it will skip if credentials are missing

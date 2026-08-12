# Daily News Social Media Poster

Automatically fetches top daily news headlines and posts them to **X (Twitter)**, **Facebook**, **Instagram**, and **LinkedIn** on a daily schedule via GitHub Actions.

## Features

- 📰 Fetches trending/top news headlines via [NewsAPI](https://newsapi.org/) (or RSS fallback)
- 🐦 Posts text updates to X.com (Twitter API v2)
- 📘 Posts to a Facebook Page (Graph API)
- 📸 Posts to Instagram Business account (Graph API — requires image)
- 💼 Posts to LinkedIn (Marketing API / Share API)
- ⏰ Runs daily via GitHub Actions cron (free for public repos)
- 🔐 All credentials stored as GitHub Secrets — never committed to code

## Project Structure

```
daily-news-poster/
├── src/
│   ├── __init__.py
│   ├── main.py              # Entry point — orchestrates fetch + post
│   ├── news_fetcher.py       # Fetches headlines from NewsAPI or RSS
│   ├── formatter.py          # Formats headlines for each platform
│   └── posters/
│       ├── __init__.py
│       ├── x_poster.py       # X.com (Twitter) posting
│       ├── facebook_poster.py# Facebook Page posting
│       ├── instagram_poster.py # Instagram posting
│       └── linkedin_poster.py  # LinkedIn posting
├── requirements.txt
├── .env.example              # Template — copy to .env for local dev
├── .github/
│   └── workflows/
│       └── daily-post.yml    # GitHub Actions daily schedule
└── README.md
```

## Prerequisites & Credentials

See [CREDENTIALS.md](CREDENTIALS.md) for a full guide on obtaining every API key/token. Below is a quick summary:

| Platform | Credentials Needed |
|---|---|
| NewsAPI | `NEWS_API_KEY` |
| X.com | `X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET` |
| Facebook | `FB_APP_ID`, `FB_APP_SECRET`, `FB_PAGE_ACCESS_TOKEN`, `FB_PAGE_ID` |
| Instagram | `IG_ACCESS_TOKEN`, `IG_BUSINESS_ACCOUNT_ID` (image required) |
| LinkedIn | `LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`, `LINKEDIN_ACCESS_TOKEN`, `LINKEDIN_REFRESH_TOKEN`, `LINKEDIN_PERSON_ID` (or org URN) |

## Setup

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/daily-news-poster.git
cd daily-news-poster
pip install -r requirements.txt
```

### 2. Get Your API Credentials

Follow [CREDENTIALS.md](CREDENTIALS.md) to set up each platform.

### 3. Local Testing

```bash
cp .env.example .env
# Fill in your .env file
python src/main.py
```

### 4. Deploy to GitHub Actions

1. Push the repo to GitHub (make it **public** for free Actions minutes)
2. Go to **Settings → Secrets and variables → Actions**
3. Add each credential as a repository secret (see `.env.example` for the full list)
4. The workflow in `.github/workflows/daily-post.yml` runs automatically at **08:00 UTC daily**
5. To test immediately: go to **Actions → Daily News Post → Run workflow**

## Customization

- **News topics**: Edit `NEWS_KEYWORDS` and `NEWS_CATEGORIES` in `.env` or `src/news_fetcher.py`
- **Post time**: Edit the cron schedule in `.github/workflows/daily-post.yml`
- **Number of headlines**: Edit `MAX_HEADLINES` (default: 3)
- **Platforms**: Set `ENABLE_X`, `ENABLE_FACEBOOK`, `ENABLE_INSTAGRAM`, `ENABLE_LINKEDIN` to `true`/`false`

## Notes

- **Instagram** requires a Business or Creator account and **cannot post text-only** — the script generates an image card from the headline. You can also supply a default background image.
- **X.com free tier** allows 1,500 posts/month — plenty for daily posts.
- **Facebook** posting requires a Page (not a personal profile).
- **LinkedIn** posting works with personal posts or organization posts.
- All APIs have rate limits — the script includes retry logic with exponential backoff.

## License

MIT

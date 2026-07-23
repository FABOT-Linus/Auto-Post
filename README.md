# Newsletter → Social Media Automation

Reads your daily news email, sends it to Claude to generate LinkedIn,
Instagram, and Reddit content (using your exact prompt spec), and posts it
automatically.

## Files

| File | Purpose |
|---|---|
| `email_reader.py` | Connects via IMAP, finds today's newsletter email, extracts clean text |
| `google_news_fetcher.py` | Fetches the top N stories from Google News' RSS feed as an alternative content source |
| `content_generator.py` | Sends the article to Claude, parses the response into per-platform content |
| `social_poster.py` | Posts to LinkedIn, Reddit, Instagram via their APIs |
| `main.py` | Orchestrates the full pipeline; supports `--dry-run`, `--schedule`, and `--source` |
| `.env.example` | Template for all required credentials |

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

## 2. Set up credentials

Copy `.env.example` to `.env` and fill in each value:

```bash
cp .env.example .env
```

**Email (Gmail example):**
1. Enable 2-Factor Authentication on your Google account.
2. Create an App Password: https://myaccount.google.com/apppasswords
3. Set `EMAIL_ADDRESS` and `EMAIL_APP_PASSWORD`.
4. Set `EMAIL_SENDER_FILTER` to the newsletter's sender address so it doesn't
   grab the wrong email.

**Anthropic API:**
1. Get a key at https://console.anthropic.com/
2. Set `ANTHROPIC_API_KEY`.

**LinkedIn:**
1. Create an app at https://www.linkedin.com/developers/apps
2. Request the "Share on LinkedIn" and "Sign In with LinkedIn using OpenID
   Connect" products.
3. Run LinkedIn's OAuth 2.0 flow once to get an access token and your
   person URN (`urn:li:person:...`).
4. Set `LINKEDIN_ACCESS_TOKEN` and `LINKEDIN_PERSON_URN`.
   Note: tokens expire (~60 days) and need refreshing.

**Reddit:**
1. Create a "script" app at https://www.reddit.com/prefs/apps
2. Set `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USERNAME`,
   `REDDIT_PASSWORD`, `REDDIT_SUBREDDIT`.

**Instagram:**
1. Convert your Instagram account to a Business or Creator account and link
   it to a Facebook Page.
2. Create a Facebook App at https://developers.facebook.com/, add the
   Instagram Graph API product.
3. Generate a long-lived Page Access Token with `instagram_content_publish`
   permission.
4. Set `IG_ACCESS_TOKEN` and `IG_BUSINESS_ACCOUNT_ID`.
5. **Important limitation:** Instagram's API requires the image to be at a
   public URL, not a local file. This script generates the image locally
   (`generate_image_from_prompt`) but you must upload it to a public host
   (S3, Cloudinary, your own server, etc.) before Instagram can publish it.
   Fill in that upload step in `main.py` where marked.

## 3. Choose your content source: email or Google News

By default the pipeline reads your newsletter email. You can instead pull
the top 5 stories straight from Google News' public RSS feed - no email
needed at all:

```bash
python main.py --source google-news --dry-run
```

Extra options for the Google News source:

```bash
# Change how many stories to pull (default 5)
python main.py --source google-news --top-n 3

# Pull from a specific section instead of general top stories
python main.py --source google-news --topic TECHNOLOGY
# valid topics: BUSINESS, TECHNOLOGY, WORLD, SPORTS, SCIENCE, HEALTH, ENTERTAINMENT

# Pull stories matching a keyword search instead
python main.py --source google-news --query "artificial intelligence"
```

All 5 (or `--top-n`) stories are combined into one digest and sent to Claude
in a single call, exactly like the newsletter email body was - Claude then
follows the same "identify the most important insight" rule from the
prompt to decide what to lead with in the LinkedIn/Instagram/Reddit posts.

Notes on this feed:
- It's public and free, no API key needed.
- It's undocumented by Google and could change format without notice -
  if `google_news_fetcher.py` starts returning nothing, check whether
  Google has changed the feed structure.
- Article links point through a `news.google.com` redirect rather than the
  publisher's URL directly - that's normal.

## 4. Test it without posting anything (works with either source)

```bash
python main.py --dry-run
```

This prints the generated LinkedIn post, Instagram prompt/caption, and
Reddit post/comment to your terminal so you can review before it ever
touches your real accounts.

## 5. Run for real

```bash
python main.py
```

Add `--instagram` to also generate the Instagram image (posting still needs
the manual upload step above filled in).

## 6. Automate it daily

Both content sources work with scheduling - just add `--source google-news`
(and any of `--top-n` / `--topic` / `--query`) to either command below.

Two options:

**Option A - built-in scheduler** (keeps a process running):
```bash
python main.py --schedule
```
Runs every day at 8:00 AM (edit the `hour`/`minute` in `main.py`'s
`run_scheduler()` to change).

**Option B - cron** (recommended for servers):
```bash
crontab -e
# Add this line to run daily at 8:00 AM:
0 8 * * * cd /path/to/social_automation && /usr/bin/python3 main.py >> run.log 2>&1
```

## 7. Run it in the cloud instead of your desktop

You don't need to keep a computer running for this. Three good options:

### Option A — GitHub Actions (free, easiest, no server to manage)

This repo includes `.github/workflows/daily-social-post.yml`, which runs the
pipeline automatically on a schedule using GitHub's free runners.

1. Push this project to a GitHub repo (private is fine).
2. Go to **Settings → Secrets and variables → Actions** and add one secret
   for every value in your `.env` file (same names: `ANTHROPIC_API_KEY`,
   `EMAIL_ADDRESS`, `LINKEDIN_ACCESS_TOKEN`, etc.).
3. That's it — it runs automatically every day at the time set in the
   workflow's `cron` line (default 8:00 AM UTC; edit it to your timezone).
4. You can also trigger it manually any time from the repo's **Actions** tab
   ("Run workflow" button) — useful for testing.
5. Check the **Actions** tab after each run to see the printed output/logs,
   same as you'd see in your terminal locally.

This is free for reasonable usage on public repos, and free up to a
generous monthly minutes quota on private repos too. Nothing runs unless
scheduled, so there's no server cost when it's idle.

### Option B — A small always-on cloud box (Railway, Render, Fly.io, a $5 VPS)

Use this if you'd rather use the built-in `--schedule` mode (keeps a Python
process running continuously with APScheduler) instead of GitHub's cron.

1. Deploy this folder to the service of your choice.
2. Set the same environment variables in their dashboard's "Environment
   Variables" / "Secrets" section.
3. Set the start command to: `python main.py --schedule --source google-news`
4. The process stays alive and fires the pipeline daily at the time set in
   `run_scheduler()` in `main.py`.

### Option C — PythonAnywhere (beginner-friendly, has a free tier)

1. Upload the project files via their file browser or `git clone`.
2. Install dependencies in a Bash console: `pip install --user -r requirements.txt`
3. Use their **Tasks** tab to schedule `python3.11 main.py --source google-news`
   to run daily at a set time — no cron/YAML knowledge needed.

Any of these three work — GitHub Actions (Option A) is the simplest if
you're already comfortable with GitHub, since there's no server to keep
alive or pay for.



- **LinkedIn tokens expire** and need periodic refreshing via OAuth.
- **Reddit** will throttle/ban accounts that post too frequently or look
  automated — read the subreddit's rules and Reddit's API terms before
  running this unattended.
- **Instagram** publishing has the extra image-hosting step described above.
- The email parser grabs the **most recent email matching today's date and
  your filters** — tune `EMAIL_SENDER_FILTER` / `EMAIL_SUBJECT_FILTER` in
  `.env` to make sure it picks up the right one.
- Always run with `--dry-run` first when testing changes — nothing gets
  posted until you're confident it's parsing/generating correctly.

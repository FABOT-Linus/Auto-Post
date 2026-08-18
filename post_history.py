"""Tracks recently-posted headlines so multiple daily runs (e.g. a 9:10am
and a 4:10pm post) don't post the same stories twice.

History is persisted to a small JSON file that the workflow commits back to
the repo after each run, so it survives between GitHub Actions jobs.
"""

import json
import logging
import os
from datetime import datetime, timedelta, timezone

log = logging.getLogger("post_history")

HISTORY_FILE = os.getenv("POST_HISTORY_FILE", "post_history.json")

# How long a headline stays "on cooldown" before it's allowed to be posted
# again. 20 hours comfortably covers a 9:10am / 4:10pm same-day pair while
# still allowing the next day's morning post to reuse a story if it's still
# actively developing.
COOLDOWN_HOURS = float(os.getenv("POST_HISTORY_COOLDOWN_HOURS", "20"))


def _normalize(title):
    return " ".join(title.lower().split())


def load_recent_titles():
    """Return the set of normalized titles posted within the cooldown window."""
    if not os.path.exists(HISTORY_FILE):
        return set()

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            entries = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        log.warning("Could not read %s (%s) — starting with empty history.", HISTORY_FILE, e)
        return set()

    cutoff = datetime.now(timezone.utc) - timedelta(hours=COOLDOWN_HOURS)
    recent = set()
    for entry in entries:
        try:
            posted_at = datetime.fromisoformat(entry["posted_at"])
        except (KeyError, ValueError):
            continue
        if posted_at >= cutoff:
            recent.add(entry["title"])

    return recent


def record_posted(headlines):
    """Append newly-posted headlines to the history file, pruning stale entries."""
    entries = []
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                entries = json.load(f)
        except (json.JSONDecodeError, OSError):
            entries = []

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=max(COOLDOWN_HOURS * 3, 72))  # keep a bit of slack history

    # Drop anything older than the extended cutoff so the file doesn't grow forever.
    pruned = []
    for entry in entries:
        try:
            posted_at = datetime.fromisoformat(entry["posted_at"])
        except (KeyError, ValueError):
            continue
        if posted_at >= cutoff:
            pruned.append(entry)

    for h in headlines:
        pruned.append({"title": _normalize(h["title"]), "posted_at": now.isoformat()})

    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(pruned, f, indent=2)
    except OSError as e:
        log.warning("Could not write %s (%s) — history not saved.", HISTORY_FILE, e)


def filter_excluding_recent(headlines, recent_titles):
    """Return only headlines whose normalized title isn't in recent_titles."""
    return [h for h in headlines if _normalize(h["title"]) not in recent_titles]

#!/usr/bin/env python3
""" Reddit Scanner — read-only, human-like, safe.

Usage:
  python3 reddit-scan.py rss            # your frontpage via RSS
  python3 reddit-scan.py sub <name>     # subreddit feed via RSS
  python3 reddit-scan.py post <id|url>  # single post + comments (browser)
  python3 reddit-scan.py posts          # your own submitted posts (browser)

SAFETY MODEL (why this exists):
  Reddit bans automation. One wrong curl, one headless browser, and your
  account is gone. Everything here is built to look human:
    - Paste is safest (no tool at all).
    - RSS needs no login and no browser.
    - Browser mode opens VISIBLE Chrome with a logged-in profile, reads,
      saves JSON+HTML, then closes immediately. The agent MUST ask before
      every browser run.
"""
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Heavy deps are imported lazily inside the functions that need them, so the
# approval gate below can run BEFORE any import — a blocked browser mode exits
# instantly even if feedparser/playwright aren't installed.

# --- Config ---
DATA_DIR = Path.home() / ".hermes" / "data" / "reddit"
LOCK_FILE = Path.home() / ".hermes" / "tmp" / "reddit-scan.lock"
PROFILE_DIR = Path.home() / ".hermes" / "reddit-profile"
CHROME_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",  # macOS
    "/usr/bin/google-chrome",        # Linux
    "/usr/bin/chromium-browser",     # Linux alt
    "/usr/bin/chromium",             # Linux alt 2
]
COOLDOWN_SECONDS = 3600   # 1 hour between browser runs
MAX_PAGE_LOADS = 3        # max navigations per browser run

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)


# --- Lock (cooldown) ---
def acquire_lock():
    if LOCK_FILE.exists():
        age = time.time() - LOCK_FILE.stat().st_mtime
        if age < COOLDOWN_SECONDS:
            remaining = int(COOLDOWN_SECONDS - age)
            print(f"LOCKED: {remaining}s remaining (cooldown {COOLDOWN_SECONDS}s)")
            sys.exit(1)
        LOCK_FILE.unlink()
    LOCK_FILE.write_text(str(time.time()))
    print(f"Lock acquired: {LOCK_FILE}")


def release_lock():
    if LOCK_FILE.exists():
        LOCK_FILE.unlink()
    print("Lock released.")


# --- Helpers ---
def timestamp():
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def extract_post_id(url_or_id):
    m = re.search(r"/comments/(\w+)/", url_or_id)
    return m.group(1) if m else url_or_id.strip()


def save_json(data, suffix):
    path = DATA_DIR / f"{timestamp()}_{suffix}.json"
    path.write_text(json.dumps(data, indent=2, default=str))
    print(f"Saved: {path}")
    return path


def save_html(html, suffix):
    path = DATA_DIR / f"{timestamp()}_{suffix}.html"
    path.write_text(html)
    print(f"Saved: {path}")
    return path


# --- Browser (visible, logged-in, read-only) ---
def launch_browser():
    from playwright.sync_api import sync_playwright
    chrome_path = None
    for p in CHROME_PATHS:
        if Path(p).exists():
            chrome_path = p
            break
    if not chrome_path:
        raise FileNotFoundError(
            "Chrome/Chromium not found. Add its path to CHROME_PATHS."
        )
    # Clear stale Singleton locks left by a crashed run.
    for f in ["SingletonLock", "SingletonSocket", "SingletonCookie"]:
        p = PROFILE_DIR / f
        if p.exists():
            p.unlink()

    p = sync_playwright().start()
    browser = p.chromium.launch_persistent_context(
        user_data_dir=str(PROFILE_DIR),
        headless=False,  # CRITICAL: headless hangs on Reddit
        executable_path=chrome_path,
        args=["--no-first-run", "--no-default-browser-check"],
    )
    page = browser.pages[0] if browser.pages else browser.new_page()

    # Enforce MAX_PAGE_LOADS.
    page_loads = [0]

    def track_load():
        page_loads[0] += 1
        if page_loads[0] > MAX_PAGE_LOADS:
            raise RuntimeError(f"Exceeded max {MAX_PAGE_LOADS} page loads")

    orig_goto = page.goto
    page.goto = lambda url, **kw: (track_load(), orig_goto(url, **kw))[1]
    return p, browser, page


# --- Mode: RSS (no browser, no login) ---
def mode_rss(feed_url):
    import feedparser
    feed = feedparser.parse(feed_url)
    entries = []
    for e in feed.entries[:25]:
        entries.append({
            "title": e.get("title", ""),
            "url": e.get("link", ""),
            "score": e.get("score", ""),
            "subreddit": e.get("source", {}).get("title", ""),
            "published": e.get("published", ""),
            "summary": e.get("summary", "")[:500],
        })
    save_json(entries, "rss")
    for e in entries:
        print(f"[{str(e['score']):>4}] {e['title'][:80]}")
    print(f"\n{len(entries)} entries from RSS.")


# --- Mode: single Post (browser) ---
def mode_post(post_id):
    url = f"https://www.reddit.com/r/all/comments/{post_id}/"
    p, browser, page = launch_browser()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)  # let JS render
        html = page.content()
        save_html(html, f"post_{post_id}")
        post_data = page.evaluate("""() => {
            const post = document.querySelector('shreddit-post');
            if (!post) return { error: 'shreddit-post not found' };
            const comments = [...document.querySelectorAll('shreddit-comment')].map(c => ({
                author: c.getAttribute('author') || 'unknown',
                score: c.getAttribute('score') || '0',
                content: (c.querySelector('[slot="comment"]')?.textContent || '').trim().slice(0, 2000),
                depth: c.getAttribute('depth') || '0',
            }));
            return {
                id: post.getAttribute('id') || '',
                title: post.getAttribute('post-title') || post.querySelector('[slot="title"]')?.textContent?.trim() || '',
                score: post.getAttribute('score') || '0',
                commentCount: post.getAttribute('comment-count') || '0',
                upvoteRatio: post.getAttribute('upvote-ratio') || '',
                subreddit: post.getAttribute('subreddit-prefixed-name') || '',
                permalink: post.getAttribute('permalink') || '',
                created: post.getAttribute('created-timestamp') || '',
                comments: comments,
            };
        }""")
        save_json(post_data, f"post_{post_id}")
        print(f"Post: {post_data.get('title', '?')}")
        print(f"Score: {post_data.get('score', '?')} | Comments: {len(post_data.get('comments', []))}")
    finally:
        browser.close()
        p.stop()
        release_lock()


# --- Mode: your own Posts (browser) ---
def mode_posts():
    url = "https://www.reddit.com/user/me/submitted/"
    p, browser, page = launch_browser()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        html = page.content()
        save_html(html, "profile_submitted")
        posts = page.evaluate("""() => {
            return [...document.querySelectorAll('shreddit-post')].map(post => {
                const permalink = post.getAttribute('permalink') || '';
                const id = (permalink.match(/\\/comments\\/(\\w+)\\//) || [])[1] || '';
                return {
                    id: id,
                    title: post.getAttribute('post-title') || '',
                    score: post.getAttribute('score') || '0',
                    commentCount: post.getAttribute('comment-count') || '0',
                    upvoteRatio: post.getAttribute('upvote-ratio') || '',
                    subreddit: post.getAttribute('subreddit-prefixed-name') || '',
                    permalink: permalink,
                    created: post.getAttribute('created-timestamp') || '',
                    postType: post.getAttribute('post-type') || '',
                };
            });
        }""")
        save_json(posts, "profile_posts")
        print(f"\nYour posts ({len(posts)}):")
        for p in posts:
            print(f" [{p['score']:>4}] {p['title'][:70]}")
    finally:
        browser.close()
        p.stop()
        release_lock()


# --- Hard approval gate for BROWSER modes ---
# Browser modes (post/posts) open a visible logged-in Chrome and can get the
# Reddit account banned if abused. They are PHYSICALLY blocked unless the user
# sets REDDIT_BROWSER_APPROVED=1 in the environment. This enforces the skill's
# "ask the user before any browser run" rule at the code level, not just in text.
BROWSER_MODES = {"post", "posts"}


def require_browser_approval(mode):
    if mode in BROWSER_MODES and os.environ.get("REDDIT_BROWSER_APPROVED") != "1":
        print(
            "BLOCKED: browser mode '%s' requires explicit user approval.\n"
            "Set REDDIT_BROWSER_APPROVED=1 in the environment to enable it, e.g.:\n"
            "  REDDIT_BROWSER_APPROVED=1 python3 reddit-scan.py %s <arg>\n"
            "This exists because browser automation can get the Reddit account banned."
            % (mode, mode)
        )
        sys.exit(2)


# --- Main ---
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    mode = sys.argv[1]
    require_browser_approval(mode)
    if mode == "rss":
        acquire_lock()
        try:
            mode_rss("https://www.reddit.com/.rss")
        finally:
            release_lock()
    elif mode == "sub":
        if len(sys.argv) < 3:
            print("Usage: reddit-scan.py sub <subreddit>")
            sys.exit(1)
        sub = sys.argv[2]
        acquire_lock()
        try:
            mode_rss(f"https://www.reddit.com/r/{sub}/.rss")
        finally:
            release_lock()
    elif mode == "post":
        if len(sys.argv) < 3:
            print("Usage: reddit-scan.py post <id|url>")
            sys.exit(1)
        post_id = extract_post_id(sys.argv[2])
        acquire_lock()
        try:
            mode_post(post_id)
        except Exception as e:
            print(f"Error: {e}")
            release_lock()
            sys.exit(1)
    elif mode == "posts":
        acquire_lock()
        try:
            mode_posts()
        except Exception as e:
            print(f"Error: {e}")
            release_lock()
            sys.exit(1)
    else:
        print(f"Unknown mode: {mode}")
        print(__doc__)
        sys.exit(1)

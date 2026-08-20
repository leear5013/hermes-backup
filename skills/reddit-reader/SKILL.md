---
name: reddit-reader
description: Use when the user wants Hermes to read Reddit — posts, comments, subreddit feeds, or their own post stats — WITHOUT getting the Reddit account banned. Read-only, human-like, safe-by-design. Enforces paste-first, RSS for feeds, and a cooldown-gated visible-browser mode for deep reads.
---

# Reddit Reader

Read Reddit from Hermes without getting banned. Reddit bans automation hard:
one wrong `curl`, one headless browser, and the account is gone. This skill is
built around one rule — **everything must look human**.

Method ranking (safest first):
1. **Paste** — copy the post/comment text into chat. Always preferred, zero risk.
2. **RSS** (`rss` / `sub`) — no browser, no login, no asking needed. Rate-limited ~1 req/30s.
3. **Browser** (`post` / `posts`) — opens VISIBLE Chrome with a logged-in profile, reads, saves JSON+HTML, closes. Agent MUST ask before each run.

## When to use each
- "what's trending on r/hermesagent?" → `reddit-scan.py sub hermesagent` (RSS, no ask)
- "summarize this thread <url>" → PASTE it, or `reddit-scan.py post <id>` (must ask first)
- "how did my posts do?" → `reddit-scan.py posts` (browser, must ask first)

## ENFORCED rules (do not skip)
1. **NEVER** `curl` Reddit, scrape `.json` endpoints, or use headless browsers.
2. **Paste is always preferred** over browser scans.
3. Before any `post` or `posts` run, **ASK the user**.
4. `rss` / `sub` need no asking (no browser, no login).
5. After a browser scan: close immediately, wait 1h before next.
6. Extract post IDs from the permalink `/comments/<id>/` — NOT the `post-id` attribute (that's the user ID; a known bug).
7. View counts exist only on the per-post page, never on profile listings. Only fetch for `post` mode, never bulk.
8. Results go to `~/.hermes/data/reddit/<timestamp>_<mode>.json`.

## Setup (one-time)
```bash
pip install playwright feedparser && playwright install chromium
mkdir -p ~/.hermes/reddit-profile ~/.hermes/data/reddit ~/.hermes/tmp
# Log into Reddit ONCE in that profile via visible Chrome:
#   google-chrome --user-data-dir="$HOME/.hermes/reddit-profile" --no-first-run --no-default-browser-check
python3 ~/.hermes/skills/reddit-reader/scripts/reddit-scan.py rss   # test
```

## Hard safety guards baked into the script
- Cooldown lock file (`~/.hermes/tmp/reddit-scan.lock`): max 1 browser run/hour.
- Max 3 page loads per browser run (monkey-patched `page.goto` raises on overflow).
- `headless=False` always (headless hangs on Reddit).
- Stale `SingletonLock`/`SingletonSocket`/`SingletonCookie` cleared before launch.

## Known quirks
- Headless crashes: renderer spins forever, `page.evaluate` never returns.
- After a killed process: orphaned Chrome helpers block the next launch →
  `pkill -9 -f "Google Chrome"` and clear locks.
- `pullpush.io` archive is dated — do not use as a fallback.

## Script
See `scripts/reddit-scan.py` (full implementation: rss / sub / post / posts modes).
Run it from the terminal tool, or have Hermes invoke it. The agent should read the
produced JSON, then report findings in chat.

## Sources
- Method + script authored by u/HolmeBengt (r/hermesagent, post 1vsiamp), documented
  in his comment replies and blog (blog.holmebengt.com, "My Complete Hermes Setup").
- Validated against the original post's safety ruleset (paste-first, RSS, visible-browser, cooldown).

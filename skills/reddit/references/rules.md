# Reddit skill — enforced rules, setup, known quirks

This is the detailed companion to the `reddit` mega-skill SKILL.md. Read it when
setting up browser mode or debugging a stuck scan. The ENFORCED RULES in SKILL.md
are the contract; this file is the implementation detail.

## Why these rules exist
Reddit bans automation. From r/hermesagent (post 1trm97s): "The API's locked down
and the .json trick 403s for me now. I got a browser-agent setup working but it
only succeeds occasionally, usually 403s otherwise." So:
- `.json` scraping is dead → use RSS (`.rss`) for feeds.
- Browser automation is flaky/bannable → visible Chrome only, ask first, cooldown.

## Method 1 — RSS (default, safe, no login)
`reddit-digest.py` and `reddit-scan.py rss|sub` read PUBLIC `.rss` feeds:
  https://www.reddit.com/r/<sub>/.rss
  https://www.reddit.com/.rss            (frontpage)
No auth, no ban risk. Rate-limited ~1 req/30s per IP — the digest script handles
429s with retry + linear backoff + 8s gaps. Reddit RSS does NOT include vote/
comment counts (only titles + links), which is fine for a digest.

## Method 2 — Browser (deep reads, ASK FIRST)
Requires ONE-TIME setup:
```bash
pip install playwright feedparser && playwright install chromium
mkdir -p ~/.hermes/reddit-profile ~/.hermes/data/reddit ~/.hermes/tmp
# Log into Reddit ONCE in that profile via VISIBLE Chrome:
#   google-chrome --user-data-dir="$HOME/.hermes/reddit-profile" \
#     --no-first-run --no-default-browser-check
python3 scripts/reddit-scan.py rss        # smoke test (RSS, no browser)
```
Browser modes (`post`, `posts`) open VISIBLE Chrome with the logged-in profile,
read, save JSON+HTML to `~/.hermes/data/reddit/`, then close.

### Hard safety guards (baked into reddit-scan.py)
- **Approval gate:** `post`/`posts` modes exit(2) unless `REDDIT_BROWSER_APPROVED=1`
  is set in the environment. The gate runs before any imports, so it blocks
  instantly even without deps installed.
- Cooldown lock file `~/.hermes/tmp/reddit-scan.lock`: max 1 browser run / hour.
- Max 3 page loads per browser run (monkey-patched `page.goto` raises on overflow).
- `headless=False` ALWAYS (headless hangs on Reddit).
- Stale `SingletonLock`/`SingletonSocket`/`SingletonCookie` cleared before launch.

### Known quirks
- Headless crashes: renderer spins, `page.evaluate` never returns.
- After a killed process: orphaned Chrome helpers block next launch →
  `pkill -9 -f "Google Chrome"` and clear locks.
- `pullpush.io` archive is dated — do not use as a fallback.
- Post IDs come from permalink `/comments/<id>/`, NOT the `post-id` attribute
  (that's the user ID — a known bug).

## File structure after setup
```
~/.hermes/
├── skills/reddit/
│   ├── SKILL.md
│   ├── references/rules.md
│   └── scripts/
│       ├── reddit-digest.py   # RSS digest (stdlib only)
│       └── reddit-scan.py     # rss / sub / post / posts
├── reddit-profile/            # logged-in Chrome session (DO NOT DELETE)
├── data/reddit/               # scan results (JSON + HTML)
└── tmp/reddit-scan.lock       # cooldown lock (auto-managed)
```

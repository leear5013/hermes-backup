---
name: reddit
description: >-
  THE single source of truth for any Reddit access from Hermes. Load this skill
  FIRST, before any other Reddit work, so the agent never gets stuck, never gets
  the account banned, and never guesses. Covers: safe RSS feeds + daily digest
  (no login, no ban risk), and a cooldown-gated visible-browser scanner for deep
  thread reads. Read-only by design. If a task involves reading Reddit — subreddit
  feeds, post/comment summaries, "what's trending", or your own post stats — load
  this skill and follow the enforced rules below.
---

# Reddit (MEGA skill — read this before touching Reddit)

Reddit bans automation hard. One wrong `curl`, one `.json` scrape, or one headless
browser, and the account is gone. **This skill is the only Reddit entry point.**
Load it before any Reddit task so you (the agent) don't fall into the 403 / ban /
headless-crash traps that bite everyone else.

> Provenance: real-world method from u/HolmeBengt (r/hermesagent post 1vsiamp)
> + the r/hermesagent thread "How are you getting Hermes to read Reddit reliably?"
> (post 1trm97s), where the OP confirmed `.json` scraping now 403s and naive
> browser agents only succeed occasionally. RSS is the ban-safe path.

## Method ranking (ALWAYS prefer the safer one)
1. **Paste** — user pastes post/comment text into chat. Zero risk, always allowed.
2. **RSS** (`reddit-digest.py` / `reddit-scan.py rss|sub`) — PUBLIC `.rss` feeds.
   No login, no API key, no ban risk. **Default for feeds + digests.**
3. **Browser** (`reddit-scan.py post|posts`) — VISIBLE Chrome + logged-in profile.
   Reads, saves JSON+HTML, closes. Agent MUST ask the user before every run.

## ENFORCED RULES (do not skip — these prevent being stuck/banned)
1. **NEVER** `curl` Reddit, scrape `.json` endpoints, or use headless browsers.
   (The `.json` trick 403s now — confirmed by the community. Headless hangs/crashes.)
2. **Paste is always preferred** over any automated scan.
3. Before any `post` or `posts` (browser) run, **ASK the user**. These modes are
   HARD-BLOCKED in code: they only run with `REDDIT_BROWSER_APPROVED=1` in the
   environment (exit 2 otherwise). Set it only after the user explicitly says yes.
4. `rss` / `sub` / `reddit-digest.py` need **no asking** (no browser, no login).
5. After a browser scan: close immediately, wait 1h before the next.
6. Extract post IDs from the permalink `/comments/<id>/` — NOT the `post-id`
   attribute (that's the USER id; a known bug).
7. View counts exist only on the per-post page, never on profile listings. Only
   fetch for `post` mode, never bulk.
8. Results go to `~/.hermes/data/reddit/<timestamp>_<mode>.json`.

## WALLS WE HIT SO YOU DON'T HAVE TO (read before improvising)
These were all hit in real use. Do NOT rediscover them:
- **`.json` endpoints are 403-dead.** `reddit.com/...json` returns 403 to scripts.
  Don't try, don't retry. Use RSS or the ArcticShift mirror.
- **RSS hides scores AND comment counts.** Titles + links only. Never promise
  "top by upvotes" from RSS data.
- **ArcticShift post scores are ingest-time snapshots** (fresh posts show score=1,
  comments=0). Useless for recent posts. For reach, count COMMENTS via
  `arctic-shift.photon-reddit.com/api/comments/search?link_id=<id>&limit=100`.
- **ArcticShift caps at limit=100 silently.** A 138-comment thread reads as 100.
  Paginate with `&before=<oldest created_utc in batch>` until a short page returns.
  (`size`, `offset`, `page`, `after` params are all invalid → HTTP 400.
  `limit>100` → HTTP 400.)
- **PullPush is 429-limited and its archive is dated.** Not a fallback.
- **Reddit RSS rate-limits per IP (429)** on rapid sequential fetches. Space
  feeds ≥8s apart; back off linearly on 429 (both bundled scripts do this).
- **Headless browsers hang on Reddit** (renderer spins forever). Visible Chrome
  only — and browser modes are hard-gated behind REDDIT_BROWSER_APPROVED=1.
- **Never loop on failures.** One failed fetch = report it and move on.

## Scripts (in this skill's scripts/ folder)
- `reddit-top.py` — **the power tool**: one command → highest-reach posts in a
  subreddit over a time window, ranked by true paginated comment counts.
  Run: `python3 scripts/reddit-top.py [sub] [hours] [top_n]`
  (defaults: hermesagent 48h top 5). Use this for "what's hot / most reached".
- `reddit-digest.py` — one-shot or scheduled digest of N subreddits via RSS.
  Stdlib-only, ban-safe, with retry/backoff for 429s.
  Run: `python3 scripts/reddit-digest.py [sub1 sub2 ...]`
  Edit `SUBS` list at the top for your interests.
- `reddit-scan.py` — 4 modes:
  `rss` (frontpage), `sub <name>` (sub feed), `post <id|url>` (single post +
  comments via browser), `posts` (your own submitted posts via browser).
  Browser modes require a logged-in Chrome profile at `~/.hermes/reddit-profile`
  and `playwright` + `feedparser` installed. See `references/rules.md` for setup.

## When the user asks...
- "what's trending on r/hermesagent?" → `reddit-digest.py hermesagent` (RSS, no ask)
- "summarize this thread <url>" → PASTE it, or `reddit-scan.py post <id>` (ask first)
- "how did my posts do?" → `reddit-scan.py posts` (browser, ask first)
- "daily digest to Telegram" → run `reddit-digest.py` on a schedule (RSS only)

## Anti-stuck checklist (if a fetch fails)
- `429 Too Many Requests` → RSS is rate-limited per IP. The digest script already
  retries with linear backoff + 8s gap. If still failing, reduce subs or wait.
- Browser won't open / hangs → must be `headless=False` (visible). Headless
  crashes on Reddit (renderer spins forever). Clear stale `SingletonLock`/
  `SingletonSocket`/`SingletonCookie` in the profile dir, or `pkill -9 -f "Google Chrome"`.
- `pullpush.io` archive is dated → do NOT use as a fallback.
- Never loop on failures. One failed fetch = report it, don't retry forever.

## Full enforced ruleset + setup
See `references/rules.md` (complete browser-setup steps, safety guards, known quirks).

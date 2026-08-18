---
name: reddit-research
description: Use when Reddit posts/comments are blocked.
version: 1.0.0
author: hermes-curator
license: MIT
metadata:
  hermes:
    tags: [reddit, scraping, arctic-shift, research]
    related_skills: [reddit-fetch, reddit-content-retrieval, web-research]
---

# Reddit Research via Arctic-Shift (verified 2026-08)

## When to Use

- User asks to search Reddit for opinions, consensus, or threads (job-hunt advice, product sentiment, community knowledge).
- You need to fetch a specific Reddit post/comment tree and anonymous endpoints are blocked (403/HTML bot-check).
- Discovery is needed across subreddits (Arctic-Shift has no working text search).

Reddit blocks anonymous access (JSON endpoints, RSS, redlib mirrors, Jina, DDG/Google/Bing from datacenter IPs). The ONLY reliable route is the Arctic-Shift archive (`arctic-shift.photon-reddit.com`) — no auth, no bot-check, includes deleted posts.

## Verified API quirks (tested from datacenter IP, 2026-08)

| Call | Status |
|---|---|
| `GET /api/posts/ids?ids=1urrb6u` | ✅ fetch post by ID (deleted included) |
| `GET /api/posts/search?subreddit=X&limit=100` | ✅ works — **limit must be ≤100** |
| `...&limit=200` | ❌ **HTTP 400 Bad Request** on many subreddits |
| `...&after=<last_post_id>` | ✅ paginate for more (repeat with last post's `id`) |
| `cscareerquestions` subreddit | ❌ **HTTP 422 Unprocessable Entity** — permanently unservable, don't loop retries |
| `GET /api/comments/search?link_id=<postid>&limit=100` | ✅ comments (bare base36 id, no `t3_` prefix) |
| `GET /api/comments/tree?link_id=X` | ✅ but data NESTED in `item["data"]` — unwrap before reading author/body |
| text search `q=` | ❌ silently ignored/broken — always sweep + filter client-side |
| `reddit.com/...json`, RSS, redlib, Jina | ❌ all bot-walled |

## Critical: read the error key

Rate-limits return `{"data": null, "error": "Timeout. Maybe slow down a bit"}` and other failures return `{"error": "HTTP Error 4xx"}` — both with `data: null`. **Treating these as "subreddit has no posts" produces false "0 posts" sweeps.** Always check for the `error` key before concluding a sub is empty. Back off 5–6s between calls; a failed call needs retries with increasing sleep (5s, 10s, 15s, 20s, 25s).

## Workflow

1. **Sweep** subreddits with the bundled script (see below) — `limit=100` + keyword regex filter client-side.
2. **Read** specific posts: `GET /api/posts/ids?ids=<id>` for the body; fetch comments when selftext is empty (question posts carry content in comments).
3. **Consensus**: bucket top comments by score, cluster into positive/negative/warning/alternative.

## Bundled script

`scripts/arctic_shift_sweep.py` — stdlib-only multi-subreddit sweep with error visibility, keyword filtering, and optional top-post comment fetching. Use it whenever `~/.hermes/scripts/reddit_search.py` is missing (it is NOT present on every box — don't assume it exists; check first).

```bash
python3 <skill_dir>/scripts/arctic_shift_sweep.py hermesagent AI_Agents \
    --kw "job|intern|portfolio" --out /opt/work/reddit_hits.json
python3 <skill_dir>/scripts/arctic_shift_sweep.py hermesagent --comments 5
```

## Fallbacks if Arctic-Shift misses

1. Wayback CDX to confirm a post exists: `https://web.archive.org/cdx/search/cdx?url=reddit.com/r/<sub>/comments/<id>*&output=json`
2. Camoufox (stealth browser, if installed on the box) for live Reddit pages — check `/data/camoufox` or the `camoufox` Python package before assuming it's unavailable.
3. old.reddit.com HTML scraping with Python regex (works for search discovery per 2026-08 tests).
4. If every route fails: report the blocker honestly — never invent post content.

## Pitfalls

- Never blind-`json.loads` a Reddit response; the API may return bot-check HTML with HTTP 200.
- Fresh posts (< 1 week) may not be archived yet.
- Do NOT dispatch subagents on redlib-mirror marathons — all bot-walled; wasted 8+ minutes in testing.
- Existing user-owned skills `reddit-fetch` / `reddit-content-retrieval` / `web-research` overlap heavily with this one; if you can edit them (`hermes curator adopt`), consolidate there instead.

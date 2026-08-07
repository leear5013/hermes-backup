---
name: reddit-content-retrieval
description: Fetch Reddit post text when anonymous access is blocked.
---

# Retrieving Reddit content behind anti-bot walls

Reddit aggressively blocks anonymous scrapers. As of 2026 two paths work: Reddit's **own RSS endpoint** (fastest, first choice) and the **Arctic-Shift** Pushshift-style archive (fallback).

## Fastest path (go here first) — Reddit's own RSS endpoint

`https://www.reddit.com/r/<subreddit>/comments/<postid>/.rss`

- Returns a valid Atom feed containing the **full post body** in the `<content>` tag — no bot-check, no login, works with just a browser User-Agent (`curl -sL -A "Mozilla/5.0 ..."`).
- **Rate-limiting quirk:** intermittently returns an EMPTY body (0 bytes) instead of an error. Do NOT conclude failure — retry 3-5 times with ~5s sleeps; it succeeds on a later attempt. (`old.reddit.com` variant also exists but returns empty more often; prefer `www`.)
- The post ID is the base36 snowflake in the permalink path (`/comments/<ID>/`); strip any `t3_` prefix.

### Extraction recipe from the `<content>` tag
The body is XML-entity-encoded inside the feed. For the exact verbatim markdown (e.g. a SOUL.md the post embeds):
1. `re.search(r'<content[^>]*>(.*?)</content>', rss, re.S)` then `html.unescape()` once → HTML like `<div class="md"><p>...</p><pre><code>...</code></pre>`.
2. Pasted files live in `<pre><code>...</code></pre>` — extract that and `html.unescape()` AGAIN (entities inside code are double-encoded, e.g. `&amp;#39;` → `'`).
3. Strip `<div class="md">` / `<p>` wrappers to reconstruct markdown. Confirm against the feed `<title>` so you know it's the right post.

Packaged one-shot helper: `scripts/fetch_reddit_rss.py <post-url-or-id> [subreddit]`.

## Fallback path — Arctic-Shift archive (if RSS is empty/unavailable)
You need the body/selftext of a Reddit post (given a permalink, share link, or comment ID `t3_...` / `1xxxxxx`) but every normal fetch returns a bot-check or error:
- `reddit.com/...json` and `old.reddit.com/...json` → HTML bot-check / "blocked by network security" (a JSON decode will fail; body is 403 HTML).
- redlib/libreddit public instances (`redlib.xyz`, `safe.reddit`, nerdvpn, etc.) → Anubis/Gandalf/Cloudflare "checking you are not a bot" pages. Nearly all are fenced now.
- CORS wrappers `api.allorigins.win` / `api.codetabs.com` → 522 / 521.
- Jina reader `r.jina.ai/URL` → "blocked by network security".
- Wayback Machine → CDX index may list a snapshot (confirming title/URL) but the captured body is often just the same verification wall.

### Arctic-Shift probe (`arctic-shift.photon-reddit.com`)
An updated Pushshift archive. Returns full post JSON including `selftext`, comments, and metadata — no auth, no bot-check.

- Get one post by ID: `GET https://arctic-shift.photon-reddit.com/api/posts/ids?ids=1urrb6u`
- Search a subreddit (recent first, useful when you only have a permalink): `GET https://arctic-shift.photon-reddit.com/api/posts/search?subreddit=hermesagent&limit=40`
- **Text search (`q=`) does NOT work** — the parameter is silently ignored by Arctic-Shift. Only `subreddit=` filtering works. If you need to find posts by topic, pull a large batch (`limit=200`) and filter in code by keywords in `title`+`selftext`. Do NOT waste time crafting text queries against Arctic-Shift.
- The post ID is the base36 snowflake in the permalink path (`/comments/<ID>/`). Strip leading `t3_` if present.
- Extract fields: `title`, `author`, `selftext` (the body), `created_utc`, `url`.

### Comments on a post
`GET https://arctic-shift.photon-reddit.com/api/comments/search?link_id=<postid>&limit=100` — `link_id` accepts the bare base36 id (no `t3_` prefix needed). Comment fields: `author`, `body`, `score`, `parent_id` (`t1_`=comment, `t3_`=post), `permalink`. Use for:
- **Empty selftext:** question posts often have NO body — all content is in the comments. Fetch comments whenever `selftext` is empty or the post reads like a question.
- **Thread reconstruction:** comments carry `parent_id` chains — map them to rebuild conversation order; sort by `score` for the best replies. The replies nested under a specific author's comments are where the real Q&A lives.

### Author research (profile a Redditor)
`GET https://arctic-shift.photon-reddit.com/api/posts/search?author=<name>&limit=100` and `.../api/comments/search?author=<name>&limit=100` — full posting/commenting history (100 per call; make both calls). Analysis pattern:
- Counter over `subreddit` field → where they live/operate.
- Sort posts by `created_utc` desc → timeline of their projects and evolution.
- Cross-reference `author` on comments for their own posts to find recurring topics/claims.
- `[removed]`/`[deleted]` entries are skipped silently — don't be confused by gaps.

## Smart Search Script (for text-based discovery)

When you need to SEARCH Reddit by topic (not just fetch by ID), use the smart search script:
```bash
python3 ~/.hermes/scripts/reddit_search.py "query" --subreddits Fitness,bodyweightfitness
```
See `references/smart-search-script.md` for details. Combines DuckDuckGo discovery + Arctic-Shift data retrieval.

## Escalation ladder (only if Arctic-Shift misses)
1. Confirm title/URL via Wayback CDX: `https://web.archive.org/cdx/search/cdx?url=reddit.com/r/<sub>/comments/<id>*&output=json`
2. Try redlib instances from the live list: `https://raw.githubusercontent.com/redlib-org/redlib-instances/main/instances.json` — but expect bot-checks on nearly all.
3. If every route is blocked, report the blocker honestly and ask the user to paste content or pick a different goal. Do NOT invent the post body.

## Pitfalls
- Reddit returns `text/html` bot-check with HTTP 200 sometimes, 403 other times — always inspect the raw body before assuming success (`read().decode(errors="replace")`); never blind `json.loads` a Reddit response.
- **Subagent proxy marathon:** when fetching a Reddit URL, do NOT dispatch a subagent to try 15+ redlib mirrors — they are all bot-walled as of 2026-08. Go straight to Arctic-Shift or RSS. The proxy-marathon wastes 8+ minutes and returns nothing useful. This was confirmed empirically (post 1urrb6u, ~15 proxy attempts, 0 successes; Arctic-Shift succeeded on first call).
- A mirror that "returns something" may be a challenge page, not content. Grep for the actual body keywords (post title, `selftext`, author) before counting it a success.
- Arctic-Shift is a third-party archive; if it is down, fall back to the ladder above rather than giving up on retrieval immediately.
- **RSS is now fully blocked (2026-08-05):** Reddit returns "Blocked" in the RSS feed, not intermittent rate-limiting. Do NOT rely on RSS as a primary fallback — it no longer works for anonymous access on most subreddits. Arctic-Shift is now the ONLY reliable route.
- **Arctic-Shift coverage is uneven** — many subreddits (fitness, loseit, xxfitness, gainit, progresspics) return 0-5 posts even with `limit=200`. Don't assume full coverage of every subreddit. If Arctic-Shift returns empty, the subreddit may simply not be well-archived.
- **Search engines block bot requests** — DuckDuckGo, Google, and Bing all serve CAPTCHA/bot challenges when scraped via curl from datacenter IPs. Do NOT waste time trying them for Reddit post discovery from VPS/cloud servers.
- **Arctic-Shift comment structure:** The `/api/comments/tree` endpoint returns comments nested as `data[].data` (kind/data wrapper), not flat. Must unwrap: `for item in response["data"]: c = item["data"]; print(c["body"])`. Accessing `item["body"]` directly gives empty strings.
- **Reddit short links** (`/s/SHORTID`) can be resolved via `curl -sL -o /dev/null -w "%{redirect_url}" <url>` to get the actual post ID.
- **When ALL routes fail:** be honest with the user. Do NOT invent post content. If the topic is well-covered in training data, you may use that knowledge while clearly stating the source is training data, not fresh Reddit pulls.
- **Overlapping skill:** `reddit-fetch` is a simpler, older version of this skill. Prefer this one (`reddit-content-retrieval`) for complex tasks — it has RSS extraction recipes, author research, and escalation ladders.
- **old.reddit.com HTML scraping (alternative):** Direct HTML scraping of `old.reddit.com` search pages and thread pages with Python regex can work (tested 2026-08). This contradicts the "Reddit web / old.reddit | ❌ 403 block" note in `reddit-fetch`. See `references/html-scraping-alternative.md` for the technique. Use as fallback when Arctic-Shift lacks coverage. Key: use search pages first to find thread URLs, then fetch individual thread HTML and parse `class="md"` content.

## Support files
- `scripts/fetch_reddit_rss.py` — one-shot fetch+extract of a post body via the RSS endpoint (handles retry + double-unescape of embedded code blocks).
- `references/arctic-shift-worked-example.md` — full worked example: failure chain table for post 1urrb6u, exact Arctic-Shift probe code, lesson learned.
- `references/redditor-profiling.md` — author-research worked example (u/NinjaAlaska): endpoint calls, analysis pattern, gotchas, output shape.
- `references/html-scraping-alternative.md` — alternative technique: direct old.reddit.com HTML scraping with Python regex (tested 2026-08). Use when Arctic-Shift lacks coverage or you need search-based discovery first.
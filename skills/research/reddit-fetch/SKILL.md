---
name: reddit-fetch
description: Use when fetching or reading Reddit posts/comments.
---

# Reddit Content — Search + Fetch

Reddit blocks anonymous scrapers on JSON/web endpoints. Use the multi-source approach below.

## Smart Search Script (use first)

```bash
python3 ~/.hermes/scripts/reddit_search.py "query here" --subreddits Fitness,bodyweightfitness,loseit
```

What it does:
- **Discovery chain**: DuckDuckGo html → Marginalia → public SearXNG (first engine with results wins)
- **Content chain per post**: Arctic-Shift → Reddit JSON → Jina Reader
- **Adaptive keyword filter**: rare query keywords (e.g. "9router") become REQUIRED — prevents generic-subreddit noise
- **Weighted scoring**: `log(upvotes+1) × (1+0.3×depth) × recency-decay`
- **Consensus report**: posts + top weighted comments + positive/negative/warning/alternative buckets
- **Caching**: 24h default (`--cache N` to override), stored in `~/.hermes/cache/reddit/`

Other modes:
```bash
python3 reddit_search.py --post <id>              # full post + top comments
python3 reddit_search.py --short <reddit_url>     # resolve short link to post id
python3 reddit_search.py "query" --min-score 3    # filter low-score posts
```

## Direct Arctic-Shift API (known IDs)

```bash
# Post by ID
curl -s "https://arctic-shift.photon-reddit.com/api/posts/ids?ids=1urrb6u"
# Full comment tree (works, data nested in item["data"])
curl -s "https://arctic-shift.photon-reddit.com/api/comments/tree?link_id=1urrb6u&limit=9999"
# Subreddit pull (no text search — returns most recent posts)
curl -s "https://arctic-shift.photon-reddit.com/api/posts/search?subreddit=bodyweightfitness&limit=100"
```

## What Works / What Doesn't (tested from datacenter IP, 2026-08)

| Method | Status |
|---|---|
| Arctic-Shift `/posts/ids` | ✅ Best for fetching by ID (includes deleted posts) |
| Arctic-Shift `/posts/search` (subreddit only) | ✅ Works, no text search — sweep + filter client-side |
| Arctic-Shift `/comments/tree?link_id=X` | ✅ Full trees — data NESTED in `item["data"]` |
| Arctic-Shift `q=` / text search | ❌ Broken (returns garbage/empty) |
| Arctic-Shift `/comments/search` | ❌ Returns empty |
| Arctic-Shift `/short_links` | ❌ Unknown query parameter for all param names — unresolved |
| Reddit JSON `.json` endpoint | ❌ 403 bot-block from datacenter IPs |
| Reddit web / old.reddit | ❌ 403 block / login redirect |
| Jina Reader `r.jina.ai` | ❌ Also 403 on Reddit (Reddit blocks Jina's fetchers) |
| DuckDuckGo `html.duckduckgo.com` | ⚠️ Was working, now HTTP 000 (blocked) — keep as first in chain, don't rely on it |
| DuckDuckGo `lite.duckduckgo.com` | ❌ Blocked |
| Google / Bing | ❌ Captcha from datacenter IPs |
| Marginalia `search.marginalia.nu` | ✅ No captcha — but small indie index, few Reddit hits |
| Public SearXNG JSON | ⚠️ Mostly antibot; some instances occasionally work |
| PRAW (official API) | ✅ Best long-term — free key at reddit.com/prefs/apps (needs account) |

**Bottom line from this server: Arctic-Shift is the ONLY reliable source.** Discovery engines are best-effort; when they fail, the script falls back to an Arctic-Shift subreddit sweep + adaptive keyword filter, which still finds the relevant posts.

## Workflow for "Search Reddit about X"

1. `python3 ~/.hermes/scripts/reddit_search.py "query" --subreddits a,b,c` — discovery + sweep + consensus in one shot
2. If the topic is niche, the adaptive filter (rare keywords required) does the work — e.g. "hermes agent 9router" correctly isolates the single relevant post from 100+ noise
3. For a specific thread: `--post <id>`
4. For deep dives: run the consensus report, then fetch individual posts with `--post` to read top comments in full

## Multi-Source Research Workflow (deep dives)

1. **Discovery**: `reddit_search.py "query" --subreddits sub1,sub2` (engine chain, then Arctic sweep fallback)
2. **Filter**: adaptive — rare keywords auto-required, common keywords all-required
3. **Fetch**: top posts via Arctic-Shift (deleted posts included!)
4. **Cluster**: script buckets comments into positive/negative/warning/alternative + ranks by `log(upvotes+1)×depth×recency`
5. **Produce consensus**: Majority opinion, minority opinion, complaints, praise, representative quotes

## Pitfalls
- Arctic-Shift text search (`q=`) is broken — sweep subreddits and filter client-side
- Arctic-Shift comments are NESTED: access via `item["data"]["author"]`, NOT `item["author"]`
- Reddit + Jina + Google + Bing + DDG are all blocked/captcha'd from datacenter IPs — don't waste time; Arctic-Shift first
- The `curl()` helper in the script can hang on blocked hosts — the script uses `_curl_limited()` with hard timeouts
- Very fresh posts (< 1 week) may not be in Arctic-Shift yet
- Short links (`/s/xxx`) are NOT resolvable via Arctic-Shift's short_links endpoint (all param names rejected)

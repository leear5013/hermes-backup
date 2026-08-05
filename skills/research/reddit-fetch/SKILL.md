---
name: reddit-fetch
description: Use when fetching or reading Reddit posts/comments.
---

# Reddit Content — Search + Fetch

Reddit blocks anonymous scrapers on JSON/web endpoints. Use the multi-source approach below.

## Smart Search Script

**Always use this first** — combines DuckDuckGo + Arctic-Shift:

```bash
python3 ~/.hermes/scripts/reddit_search.py "query here" --subreddits Fitness,bodyweightfitness,loseit
```

- Searches DuckDuckGo for Reddit URLs + pulls from Arctic-Shift subreddits
- Returns post IDs, titles, scores, URLs
- No API keys needed

## Fetch Full Post + Comments

```bash
python3 ~/.hermes/scripts/reddit_search.py --post <post_id>
```

Returns full post body + top comments sorted by score.

## Direct Arctic-Shift API (for specific known IDs)

```bash
# Post by ID
curl -s "https://arctic-shift.photon-reddit.com/api/posts/ids?ids=1urrb6u"
# Comments on a post
curl -s "https://arctic-shift.photon-reddit.com/api/comments/search?link_id=1urrb6u&limit=50"
# Subreddit pull (no text search — only returns recent posts)
curl -s "https://arctic-shift.photon-reddit.com/api/posts/search?subreddit=bodyweightfitness&limit=100"
```

## What Works / What Doesn't

| Method | Status |
|---|---|
| Arctic-Shift `/posts/ids` | ✅ Best for fetching by ID |
| Arctic-Shift `/posts/search` (subreddit only) | ✅ Works, but no text search |
| Arctic-Shift `/posts/search?q=...` | ❌ Broken — returns empty |
| Reddit JSON `.json` endpoint | ❌ 403 bot-block |
| Reddit RSS feeds | ❌ Rate-limited/blocked |
| DuckDuckGo lite for Reddit URLs | ✅ Works as discovery layer |
| redlib/libreddit mirrors | ❌ All behind bot challenges |
| PRAW (official API) | ✅ Needs free API key (reddit.com/prefs/apps) |

## Workflow for "Search Reddit about X"

1. Run `reddit_search.py "query"` — gets results from DDG + Arctic-Shift
2. Pick the most relevant post IDs
3. Run `reddit_search.py --post <id>` for full content + comments
4. If Arctic-Shift misses a post, try RSS as last resort

## Pitfalls
- Arctic-Shift text search (`q=` parameter) is broken — don't use it
- Reddit JSON/RSS endpoints are blocked from this server
- DuckDuckGo lite sometimes shows bot challenges — retry after a few seconds
- For very fresh posts (< 1 week), Arctic-Shift may not have them yet

---
name: reddit-fetch
description: Use when fetching or reading Reddit posts/comments.
---

# Fetching Reddit content reliably

Reddit blocks anonymous scrapers on its JSON/web endpoints (403 "blocked by network security", Cloudflare "Just a moment", Anubis/Gandalf bot-checks on mirrors). The routes below WORK as of 2026-08; all redlib mirrors and CORS proxies (allorigins/codetabs/Jina) are bot-walled and NOT worth trying.

## Working routes (in order)

### 1. Arctic-Shift API (fastest, full JSON) — PREFERRED
Reddit data archive. No auth, reliable, full post body + comments.

```bash
# Post by ID
curl -s "https://arctic-shift.photon-reddit.com/api/posts/ids?ids=1urrb6u"
# Search by subreddit (recent posts)
curl -s "https://arctic-shift.photon-reddit.com/api/posts/search?subreddit=hermesagent&limit=40"
# Comments on a post
curl -s "https://arctic-shift.photon-reddit.com/api/comments/search?link_id=1urrb6u&limit=5"
```

Response: `{"data":[...]}`. Post fields: `title`, `author`, `selftext` (full body), `url`, `score`, `created_utc`, `link_flair_text`.

### 2. Reddit RSS feed (fallback for very fresh posts)
```bash
curl -sL -A "Mozilla/5.0 (Windows NT 10.0; Win64; x64)" "https://www.reddit.com/r/hermesagent/comments/1urrb6u/.rss"
```
Intermittently rate-limits (empty response) — retry after a few seconds. Content is HTML-escaped inside XML; strip tags/unescape.

### 3. Share links `/s/<code>`
Resolve the redirect first (`curl -s -o /dev/null -w "%{redirect_url}"`), extract the `/comments/<id>/` segment, then use route 1 or 2 with that ID.

## Pitfalls
- **Never** use the JSON endpoint directly (`www.reddit.com/.../comments/<id>.json`) — 403 bot-block.
- redlib/libreddit/teddit public instances: all behind Anubis/Gandalf/Cloudflare challenges → skip.
- allorigins (522), codetabs (521), r.jina.ai (Cloudflare), pullpush (rate-limit/paid), Wayback (usually no snapshot) → skip.
- Comments need `link_id` = the post's base36 ID (from the URL or post `id` field).
- If Arctic-Shift returns empty for a brand-new post, fall back to RSS, then wait and retry.

## Worked example (2026-08-04)
r/hermesagent post `1urrb6u` ("This Simple SOUL.md Tweak...") fetched via Arctic-Shift `/api/posts/ids` in one call after ~15 failed proxy attempts. Subagent independently confirmed via RSS route. Don't repeat the proxy marathon — go straight to Arctic-Shift.

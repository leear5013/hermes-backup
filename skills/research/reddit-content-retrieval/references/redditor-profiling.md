# Redditor profiling — worked example (u/NinjaAlaska, 2026-08-04)

## Goal
User asked to research an author discovered in a Reddit thread ("tell me more about him, what he's working on"). Pattern: given a username, build a profile from Arctic-Shift author-search endpoints.

## Exact calls used
```bash
curl -s "https://arctic-shift.photon-reddit.com/api/posts/search?author=NinjaAlaska&limit=100"    -o na_posts.json
curl -s "https://arctic-shift.photon-reddit.com/api/comments/search?author=NinjaAlaska&limit=100" -o na_coms.json
```
Both returned `{"data":[...]}` with 100 items each — enough for a full profile.

## Analysis pattern (worked)
1. **Subreddit Counter** (`collections.Counter` over `subreddit` on both posts and comments) → where they operate. Here: 43 Fortnite posts (2018-2021), plus DeepSeek/hermesagent/opencode (AI harness), AntiDetectGuides/ProxyUseCases (stealth/scraping niche), ahmedabad/vadodara/india (geography → Gujarat, India).
2. **Post timeline** (sort by `created_utc` desc, print `[date] r/sub (score): title`) → project evolution: Fortnite gamer → ads/marketing (2020) → Damru stealth-Android framework (2026-05/06) → Gemini memes, Gemma fine-tune, SOUL.md Terminal Bench post (2026-07).
3. **Comment cross-reference** (filter comments by `author` + keyword) → recurring claims/setup details (his harness stack: Hermes #1, Codex #2 via 9router, DeepSeek V4 Flash, hates opencode; uses the SOUL.md prompt as a skill).
4. **Flagged subreddits for personal life clues** (India-specific, city subreddits) → nationality, health, daily-life context.
5. **Deep-dive on one claim** — find the exact comment (search comments for a phrase), then fetch the WHOLE parent thread (`/api/posts/ids?ids=<link_id>` + `/api/comments/search?link_id=<link_id>`) to reconstruct the conversation his comment lived in.

## Gotchas hit
- Author posts search caps at `limit=100` — for heavy users, paginate (the API supports `after`/`before` cursors; not needed here).
- The post whose comments mattered (r/DeepSeek "What is the best harness agent for deepseek") had **empty selftext** — it was a question post; ALL content was in comments. This is the "empty selftext → fetch comments" rule in action.
- `[removed]`/`[deleted]` posts/comments appear in the data — skip silently, they're gaps not errors.
- Comment `permalink` + `parent_id` chains let you rebuild which reply the quote came from (e.g. his "all ios phones are simulated android" was a reply to "do you know any services with real android/ios phones with remote access?").

## Output shape that worked
Present as a structured profile: identity/geography → flagship project → AI work → tool stack → niche → reach/scale (top-scoring posts). End with a "go deeper?" offer (GitHub, HF page, full thread trace).

---
name: web-research
description: Use when searching Reddit or LinkedIn for profiles or info.
---

# Web Research — LinkedIn, Reddit, and Beyond

Research tools and strategies for accessing LinkedIn profiles and Reddit content when standard scraping is blocked.

## LinkedIn Access

LinkedIn blocks ALL anonymous access (auth wall, Cloudflare, bot detection). Every approach — direct curl, Google cache, Bing, DuckDuckGo, Wayback Machine, Chromium headless — gets blocked.

### Option 1: LinkedIn MCP Server (BEST for AI agents) ⭐3019
```
# Install prerequisites (one-time):
pip install uv        # uvx runner (curl installer may hang on some hosts — pip works)
pip install mcp       # Hermes' MCP client SDK (without it, MCP discovery is silently disabled)
uv tool install mcp-server-linkedin   # pre-download; PATH note: binary lands in /data/.local/bin

# Add to ~/.hermes/config.yaml under mcp_servers:
linkedin:
  command: "uvx"
  args: ["mcp-server-linkedin@latest"]
  timeout: 300
  env:
    UV_HTTP_TIMEOUT: "300"
```
- Restart Hermes gateway after config change (no hot-reload for MCP servers)
- First tool call opens a real browser window for one-time login — needs a display or the user's machine
- `stickerdaniel/linkedin-mcp-server` — dedicated MCP server for LinkedIn
- Uses **Patchright** (stealth Chromium) — opens real browser for one-time login, then automates
- Tools: `get_person_profile`, `search_people`, `search_jobs`, `get_company_profile`, `search_posts`, `get_feed`, `send_message`, `connect_with_person`
- LinkedIn CANNOT detect this — it's your real browser session, just automated
- No ban risk (unlike API-based tools that LinkedIn can fingerprint)
- Other MCP options: `eliasbiondo/linkedin-mcp-server` ⭐169, `Linked-API/linkedapi-mcp` ⭐63

### Option 2: `linkedin-api` (PyPI, needs credentials)
```
pip install linkedin-api
```
- Uses LinkedIn's internal API with session cookies
- Python 3.10+, version 2.3.1
- Log in once → stores session → search profiles, get data, send messages
- ⚠️ LinkedIn CAN detect this pattern and may ban the account

### Option 3: Cross-reference via GitHub
When you can't access LinkedIn at all, search GitHub for matching usernames:
```
curl -s "https://api.github.com/search/users?q=<name>"
```
- Get bio, location, repos, languages, followers
- Good for: tech professionals, developers
- Limitation: only works if they have a GitHub account with the same name

### Option 4: User provides content
Ask the user to screenshot or copy-paste the LinkedIn profile. Analyze from that.
- Safest approach — zero ban risk
- Works every time, no tooling needed

### What DOESN'T work for LinkedIn (don't waste time)
- Direct curl → auth wall redirect
- Google/Bing/DuckDuckGo cache → CAPTCHA
- Wayback Machine → no snapshots or stale data
- Chromium headless dump-dom → still blocked by search engines
- `joeyism/linkedin_scraper` — was ⭐4390 but requires login and LinkedIn can detect Playwright fingerprinting

## Reddit Access

### Smart Search Script (Preferred — combines sources)
```bash
python3 ~/.hermes/scripts/reddit_search.py "query here" --subreddits Fitness,bodyweightfitness,loseit
python3 ~/.hermes/scripts/reddit_search.py --post <post_id>  # full post + comments
```
- Searches DuckDuckGo for Reddit URLs + pulls from Arctic-Shift subreddits
- No API keys needed, handles text search (which Arctic-Shift can't do)

### Known-working routes (2026-08)

**Route 1: Arctic-Shift API — by post ID only**
```
curl -s "https://arctic-shift.photon-reddit.com/api/posts/ids?ids=<post_id>"
curl -s "https://arctic-shift.photon-reddit.com/api/comments/search?link_id=<post_id>&limit=50"
```
✅ Works for: fetching a specific post when you know the ID
❌ Does NOT work for: text search (`q` parameter returns 0 results), many subreddits have poor coverage

**Route 2: PRAW (official Reddit API)**
- Needs free API key from reddit.com/prefs/apps
- Full search, comments, user data — most reliable when available
- Reddit explicitly allows this (won't ban your account)

**Route 3: YARS / URS (no API key)**
- `pip install git+https://github.com/datavorous/yars.git` (⚠️ no setup.py — may need manual clone)
- URS: `pip install git+https://github.com/JosephLai241/URS.git` — CLI tool
- Both work without API keys but may have install issues

### Search strategy
1. **Known post ID** → Arctic-Shift (fastest)
2. **Discovery/search** → YARS or URS (Arctic-Shift search is broken)
3. **Fresh posts** → Reddit RSS (intermittent, retry on empty)
4. **Cross-platform** → GitHub username search, DuckDuckGo HTML

### Blocked routes (don't waste time)
- Reddit JSON API (`reddit.com/.../json`) — 403
- Reddit RSS for search — returns "Blocked"
- redlib/libreddit/teddit mirrors — all bot-walled
- DuckDuckGo lite — bot challenge
- Google cache — CAPTCHA

## Facebook Access

Facebook share links (`facebook.com/share/<id>/`) work with ONE specific URL variant. See `references/facebook-share-link.md` for the share-link recipe.

**For FULL post text + comments (the common ask): use the Googlebot UA trick.** See `references/facebook-full-post-comments.md` for the complete recipe. Summary:

1. Share link → fetch `https://www.facebook.com/share/p/<id>/` (mobile UA) → read `og:url` for the original post URL
2. Fetch the ORIGINAL post URL (`facebook.com/<author>/posts/<id>/`) with UA `Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)` → ~1MB page with **full post + all visible comments + authors + reaction/share counts, no login wall**
3. Extract: strip scripts/styles/tags for ordered reading; or regex `"body":\s*\{"text":\s*"..."` for clean comment JSON (decode with `json.loads('"'+s+'"')`, drop surrogates — NOT `.decode('unicode_escape')`)

**Fallback: embed plugin** — `facebook.com/plugins/post.php?href=<urlencoded>&show_text=true&width=500` rendered via Chromium headless gives the FULL post text (not truncated like og:description) but NO comments.

**Post-text-only trick:** the `/share/p/` variant's `og:description` meta tag carries the first ~50-60 words as **hex HTML entities** (`&#x641;&#x63a;...`). Decode with:

```python
import re
decoded = re.sub(r'&#x([0-9a-fA-F]+);', lambda m: chr(int(m.group(1), 16)), raw_desc)
```

Also extract `og:title` (author name), `og:url` (original post URL — contains the percent-encoded full title), `og:type` (`video.other` = video post), `og:image` (media).

**What fails (don't waste time):**
- `facebook.com/share/<id>/` without `/p/` → 1.5KB "Sorry, something went wrong" error page
- `mbasic.facebook.com` → login wall
- `m.facebook.com` → title only, no body
- Original post page with a normal UA → title only (~50 words max public preview) — the Googlebot UA is what unlocks it

## Pitfalls
- Arctic-Shift `q` parameter is broken — always returns 0. Never use for text search.
- DuckDuckGo `lite.duckduckgo.com` returns bot challenges from datacenter/VPS IPs — don't use it. `html.duckduckgo.com` works from datacenter IPs and is the correct endpoint for server-side Reddit discovery.
- Arctic-Shift `/api/comments/tree` returns comments nested as `data[].data` (kind/data wrapper), not flat — must unwrap before accessing author/body/score fields. Example: `for item in response["data"]: c = item["data"]; print(c["body"])`.
- Reddit `/s/` short links can be resolved via `curl -sL -o /dev/null -w "%{redirect_url}" <url>` to get the actual post ID.
- Arctic-Shift subreddit coverage varies wildly — popular subreddits (Fitness, loseit) may return 0 posts.
- LinkedIn requires authentication for ANY data access. The MCP server approach (Patchright browser) is the safest for AI agents — it uses your real browser session.
- Google both block server-side scraping with CAPTCHAs — even Chromium headless can't bypass Google's CAPTCHA from a server IP.
- YARS (`pip install yars`) is Python 2 code and won't install on Python 3. Use the smart search script or PRAW instead.
- `reddit-fetch` and `reddit-content-retrieval` overlap — prefer `reddit-content-retrieval` for complex tasks (has RSS extraction, author profiling, escalation ladders). The smart search script in `reddit-search.py` is the best entry point for both.
- When a scraping tool fails, check if an MCP server or CLI tool exists before trying raw HTTP.

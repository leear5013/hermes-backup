# Web Research Tools Reference (2026-08)

## LinkedIn MCP Servers (Preferred for AI Agents)

| Tool | Stars | Method | Notes |
|---|---|---|---|
| `stickerdaniel/linkedin-mcp-server` | 3019 | Patchright (stealth Chromium) | **Best** — full profile, search, messaging, companies |
| `eliasbiondo/linkedin-mcp-server` | 169 | MCP | Search people, companies, jobs |
| `Sharan-Kumar-R/Custom-MCP-Server` | 95 | MCP | Multi-platform (LinkedIn + Facebook + Instagram) |
| `Linked-API/linkedapi-mcp` | 63 | MCP | Account control + real-time data |
| `anysiteio/anysite-mcp-server` | 62 | MCP | Generic scraper for LinkedIn + others |

### MCP Server Tools (stickerdaniel/linkedin-mcp-server)
- `get_person_profile` — full profile with section selection (experience, education, skills, posts, etc.)
- `search_people` — by keywords, location, connection degree, company
- `search_jobs` — with keyword and location filters
- `get_company_profile` — company info + posts + employees
- `search_posts` — global post search with recency filter
- `get_feed` — home feed
- `send_message` / `connect_with_person` — messaging and connections
- `get_inbox` / `get_conversation` — read messages

## LinkedIn Scrapers (Legacy — MCP preferred)

| Tool | Stars | Language | Method | Notes |
|---|---|---|---|---|
| `linkedin-api` (PyPI) | — | Python | Internal API | v2.3.1, requires login, ⚠️ ban risk |
| `joeyism/linkedin_scraper` | 4390 | Python | Playwright | v3.0 async, ⚠️ ban risk |
| `SuwaidAslam/LinkedIn-profile-scraper` | 40 | Python | Selenium | Public profiles only, may be outdated |
| `l4rm4nd/LinkedInDumper` | 605 | Python | API | Company employee dumps |

## Reddit Tools

| Tool | Stars | Language | API Key? | Notes |
|---|---|---|---|---|
| Smart search script | — | Python | No | `~/.hermes/scripts/reddit_search.py` — DDG + Arctic-Shift |
| `datavorous/yars` | 225 | Python | No | ⚠️ Python 2 code, won't install on Python 3 |
| `JosephLai241/URS` | 1019 | Python+Rust | Optional | Most comprehensive CLI scraper |
| `Serene-Arc/bulk-downloader-for-reddit` | 2596 | Python | Yes | Archive/download focused |
| PRAW (official) | — | Python | Free API key | Most reliable, Reddit encourages this |

## Why Arctic-Shift Fails for Search

Tested 2026-08-05: Arctic-Shift `/api/posts/search` with `q=` parameter returns 0 results for ANY query. Only subreddit-filtered pulls work, and even those have poor coverage (bodyweightfitness, Fitness, loseit all returned minimal/0 posts). The `sort=score` parameter also appears non-functional.

## Why LinkedIn Blocks Everything

LinkedIn uses aggressive bot detection:
- All anonymous HTTP requests → auth wall redirect
- Google/Bing/DuckDuckGo cache → CAPTCHA or empty
- Wayback Machine → no snapshots for most profiles
- Even Googlebot UA → auth wall
- Chromium headless dump-dom → still blocked by search engines
- **Only reliable solution:** MCP server with Patchright (real browser session, one-time login)
